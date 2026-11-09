import json
from datetime import datetime
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from members.permissions import IsApprovedMember
from sheets_storage import SheetsRepository, sheets_enabled
from .models import Ballot, Candidate, Election, VoterParticipation
from .serializers import ElectionSerializer, VoteSubmissionSerializer


def _repo():
    return SheetsRepository()


def _parse_time(value):
    if not value:
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _election_payload(row, member_id=None, repo=None):
    now = timezone.now()
    starts = _parse_time(row.get("starts_at"))
    ends = _parse_time(row.get("ends_at"))
    active = str(row.get("is_active", "")).lower() in {"1", "true", "yes"}
    is_open = bool(starts and ends and active and starts <= now <= ends)
    status_label = "ملغاة" if not active else ("قادمة" if starts and now < starts else ("مفتوحة" if ends and now <= ends else "منتهية"))
    candidates = row.get("candidates", [])
    has_voted = repo.has_voted(row.get("id"), member_id) if repo and member_id else False
    return {"id": row.get("id"), "title": row.get("title", ""), "description": row.get("description", ""), "max_choices": int(row.get("max_choices") or 1), "starts_at": row.get("starts_at"), "ends_at": row.get("ends_at"), "is_active": active, "is_open": is_open, "status_label": status_label, "results_public": str(row.get("results_public", "")).lower() in {"1", "true", "yes"}, "candidates": candidates, "has_voted": has_voted, "eligible_to_vote": bool(member_id)}


class ElectionListView(generics.ListAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        if sheets_enabled():
            member = getattr(request.user, "member_profile", None)
            repo = _repo()
            return Response([_election_payload(row, member.pk if member else None, repo) for row in repo.elections()])
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Election.objects.prefetch_related("candidates__member").order_by("-starts_at")


class ElectionDetailView(generics.RetrieveAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        if sheets_enabled():
            member = getattr(request.user, "member_profile", None)
            row = _repo().election(kwargs["pk"])
            if not row:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response(_election_payload(row, member.pk if member else None, _repo()))
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        return Election.objects.prefetch_related("candidates__member")


class VoteView(APIView):
    permission_classes = [IsApprovedMember]

    @transaction.atomic
    def post(self, request, pk):
        if sheets_enabled():
            voter = request.user.member_profile
            repo = _repo()
            election = repo.election(pk)
            if not election:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            payload = _election_payload(election, voter.pk, repo)
            if not payload["is_active"] or payload["status_label"] == "قادمة":
                return Response({"detail": "الانتخابات لم تبدأ بعد."}, status=status.HTTP_400_BAD_REQUEST)
            if payload["status_label"] == "منتهية":
                return Response({"detail": "انتهت فترة التصويت."}, status=status.HTTP_400_BAD_REQUEST)
            if repo.has_voted(pk, voter.pk):
                return Response({"detail": "لقد صوّتت مسبقاً في هذه الانتخابات."}, status=status.HTTP_409_CONFLICT)
            candidate_ids = request.data.get("candidate_ids", [])
            if not isinstance(candidate_ids, list) or not candidate_ids or len(candidate_ids) != len(set(candidate_ids)) or len(candidate_ids) > payload["max_choices"]:
                return Response({"detail": "اختيارات التصويت غير صالحة."}, status=status.HTTP_400_BAD_REQUEST)
            valid_ids = {str(c.get("id")) for c in election.get("candidates", [])}
            if any(str(candidate_id) not in valid_ids for candidate_id in candidate_ids):
                return Response({"detail": "تتضمن اختياراتك مرشحاً غير صالح لهذه الانتخابات."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                repo.record_vote(pk, voter.pk, candidate_ids)
            except ValueError:
                return Response({"detail": "لقد صوّتت مسبقاً في هذه الانتخابات."}, status=status.HTTP_409_CONFLICT)
            return Response({"detail": "تم تسجيل صوتك بنجاح. لا يمكن تغيير الاختيار بعد إرساله."}, status=status.HTTP_201_CREATED)
        election = get_object_or_404(Election.objects.select_for_update(), pk=pk)
        now = timezone.now()
        if not election.is_active or now < election.starts_at:
            return Response({"detail": "الانتخابات لم تبدأ بعد."}, status=status.HTTP_400_BAD_REQUEST)
        if now > election.ends_at:
            return Response({"detail": "انتهت فترة التصويت."}, status=status.HTTP_400_BAD_REQUEST)
        voter = request.user.member_profile
        if VoterParticipation.objects.filter(election=election, voter=voter).exists():
            return Response({"detail": "لقد صوّتت مسبقاً في هذه الانتخابات."}, status=status.HTTP_409_CONFLICT)
        serializer = VoteSubmissionSerializer(data=request.data, context={"election": election})
        serializer.is_valid(raise_exception=True)
        candidate_ids = serializer.validated_data["candidate_ids"]
        candidates = list(Candidate.objects.filter(election=election, id__in=candidate_ids))
        if len(candidates) != len(candidate_ids):
            return Response({"detail": "تتضمن اختياراتك مرشحاً غير صالح لهذه الانتخابات."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                VoterParticipation.objects.create(election=election, voter=voter)
                ballot = Ballot.objects.create(election=election)
                ballot.candidates.set(candidates)
        except IntegrityError:
            return Response({"detail": "لقد صوّتت مسبقاً في هذه الانتخابات."}, status=status.HTTP_409_CONFLICT)
        return Response({"detail": "تم تسجيل صوتك بنجاح. لا يمكن تغيير الاختيار بعد إرساله."}, status=status.HTTP_201_CREATED)


class ElectionResultsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        if sheets_enabled():
            repo = _repo()
            election = repo.election(pk)
            if not election:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            payload = _election_payload(election)
            if not (payload["results_public"] or not payload["is_open"] or request.user.is_staff):
                return Response({"detail": "النتائج غير متاحة بعد."}, status=status.HTTP_403_FORBIDDEN)
            rows, total_ballots, total_selections = repo.results(pk)
            return Response({"election": payload["title"], "status": payload["status_label"], "total_ballots": total_ballots, "total_participants": total_ballots, "total_selections": total_selections, "results": [{"candidate_id": row.get("id"), "name": row.get("name", ""), "family_name": row.get("family_name", ""), "votes": row["votes"], "percent": round(row["votes"] * 100 / total_selections, 1) if total_selections else 0} for row in rows]})
        election = get_object_or_404(Election, pk=pk)
        if not (election.results_public or not election.is_open or request.user.is_staff):
            return Response({"detail": "النتائج غير متاحة بعد."}, status=status.HTTP_403_FORBIDDEN)
        counts = list(Candidate.objects.filter(election=election).select_related("member").annotate(votes=Count("ballots", distinct=True)).order_by("-votes", "member__full_name"))
        total_ballots = Ballot.objects.filter(election=election).count()
        total_selections = sum(candidate.votes for candidate in counts)
        return Response({"election": election.title, "status": election.status_label, "total_ballots": total_ballots, "total_participants": VoterParticipation.objects.filter(election=election).count(), "total_selections": total_selections, "results": [{"candidate_id": candidate.id, "name": candidate.member.full_name, "family_name": candidate.member.family_name, "votes": candidate.votes, "percent": round(candidate.votes * 100 / total_selections, 1) if total_selections else 0} for candidate in counts]})
