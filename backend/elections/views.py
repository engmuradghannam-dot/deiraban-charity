from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from members.permissions import IsApprovedMember
from .models import Election, Candidate, Ballot
from .serializers import ElectionSerializer


class ElectionListView(generics.ListAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Election.objects.prefetch_related(
            'candidates__member'
        ).order_by('-starts_at')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class ElectionDetailView(generics.RetrieveAPIView):
    serializer_class = ElectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Election.objects.prefetch_related('candidates__member')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class VoteView(APIView):
    """تسجيل صوت العضو — صوت واحد فقط، بعدد خيارات <= max_choices."""
    permission_classes = [IsApprovedMember]

    @transaction.atomic
    def post(self, request, pk):
        election = get_object_or_404(
            Election.objects.select_for_update(), pk=pk
        )
        now = timezone.now()
        if not election.is_active or now < election.starts_at:
            return Response({'detail': 'الانتخابات لم تبدأ بعد.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if now > election.ends_at:
            return Response({'detail': 'انتهت فترة التصويت.'},
                            status=status.HTTP_400_BAD_REQUEST)

        voter = request.user.member_profile
        if Ballot.objects.filter(election=election, voter=voter).exists():
            return Response({'detail': 'لقد صوّتت مسبقاً في هذه الانتخابات.'},
                            status=status.HTTP_400_BAD_REQUEST)

        candidate_ids = request.data.get('candidate_ids', [])
        if not isinstance(candidate_ids, list) or not candidate_ids:
            return Response({'detail': 'اختر مرشحاً واحداً على الأقل.'},
                            status=status.HTTP_400_BAD_REQUEST)
        candidate_ids = list(dict.fromkeys(int(c) for c in candidate_ids))
        if len(candidate_ids) > election.max_choices:
            return Response(
                {'detail': f'يمكنك اختيار {election.max_choices} مرشحين كحد أقصى.'},
                status=status.HTTP_400_BAD_REQUEST)

        candidates = list(Candidate.objects.filter(
            election=election, id__in=candidate_ids
        ))
        if len(candidates) != len(candidate_ids):
            return Response({'detail': 'مرشح غير صالح.'},
                            status=status.HTTP_400_BAD_REQUEST)

        ballot = Ballot.objects.create(election=election, voter=voter)
        ballot.candidates.set(candidates)
        return Response({'detail': 'تم تسجيل صوتك بنجاح. شكراً لمشاركتك.'},
                        status=status.HTTP_201_CREATED)


class ElectionResultsView(APIView):
    """نتائج الفرز — متاحة بعد انتهاء التصويت أو إذا كانت علنية."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        election = get_object_or_404(Election, pk=pk)
        if not (election.results_public or not election.is_open
                or request.user.is_staff):
            return Response({'detail': 'النتائج غير متاحة بعد.'},
                            status=status.HTTP_403_FORBIDDEN)

        counts = (Candidate.objects.filter(election=election)
                  .annotate(votes=Count('ballots'))
                  .order_by('-votes'))
        total = Ballot.objects.filter(election=election).count()
        return Response({
            'election': election.title,
            'status': election.status_label,
            'total_ballots': total,
            'results': [{
                'candidate_id': c.id,
                'name': c.member.full_name,
                'family_name': c.member.family_name,
                'votes': c.votes,
            } for c in counts],
        })
