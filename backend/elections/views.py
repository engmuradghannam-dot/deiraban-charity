from django.db import IntegrityError, transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from members.permissions import IsApprovedMember
from .models import Ballot, Candidate, Election, VoterParticipation
from .serializers import ElectionSerializer, VoteSubmissionSerializer


class ElectionListView(generics.ListAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Election.objects.prefetch_related("candidates__member").order_by("-starts_at")


class ElectionDetailView(generics.RetrieveAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Election.objects.prefetch_related("candidates__member")


class VoteView(APIView):
    """يسجل ورقة واحدة ضمن فترة انتخاب مفتوحة للعضو المعتمد."""

    permission_classes = [IsApprovedMember]

    @transaction.atomic
    def post(self, request, pk):
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
            # سجل المشاركة يمنع التكرار؛ ورقة الاقتراع لا تحمل هوية الناخب أو توقيت إرساله.
            with transaction.atomic():
                VoterParticipation.objects.create(election=election, voter=voter)
                ballot = Ballot.objects.create(election=election)
                ballot.candidates.set(candidates)
        except IntegrityError:
            return Response({"detail": "لقد صوّتت مسبقاً في هذه الانتخابات."}, status=status.HTTP_409_CONFLICT)

        return Response(
            {"detail": "تم تسجيل صوتك بنجاح. لا يمكن تغيير الاختيار بعد إرساله."},
            status=status.HTTP_201_CREATED,
        )


class ElectionResultsView(APIView):
    """يعرض النتائج المجمعة عند إعلانها أو بعد إغلاق الانتخاب."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        election = get_object_or_404(Election, pk=pk)
        if not (election.results_public or not election.is_open or request.user.is_staff):
            return Response({"detail": "النتائج غير متاحة بعد."}, status=status.HTTP_403_FORBIDDEN)

        counts = list(
            Candidate.objects.filter(election=election)
            .select_related("member")
            .annotate(votes=Count("ballots", distinct=True))
            .order_by("-votes", "member__full_name")
        )
        total_ballots = Ballot.objects.filter(election=election).count()
        total_selections = sum(candidate.votes for candidate in counts)
        return Response({
            "election": election.title,
            "status": election.status_label,
            "total_ballots": total_ballots,
            "total_participants": VoterParticipation.objects.filter(election=election).count(),
            "total_selections": total_selections,
            "results": [
                {
                    "candidate_id": candidate.id,
                    "name": candidate.member.full_name,
                    "family_name": candidate.member.family_name,
                    "votes": candidate.votes,
                    "percent": round(candidate.votes * 100 / total_selections, 1) if total_selections else 0,
                }
                for candidate in counts
            ],
        })
