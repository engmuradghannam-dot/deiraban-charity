from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from .models import Family, Member
from .serializers import FamilySerializer, MemberSerializer


class FamilyViewSet(viewsets.ModelViewSet):
    queryset = Family.objects.annotate(members_count=Count("members")).order_by("name")
    serializer_class = FamilySerializer
    search_fields = ["name"]


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.select_related("family").all()
    serializer_class = MemberSerializer
    filterset_fields = ["family", "status"]
    search_fields = ["full_name", "membership_number", "national_id"]
    ordering_fields = ["membership_number", "full_name"]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """إحصائية سريعة: عدد الأعضاء حسب الحالة وحسب العائلة"""
        by_status = list(
            Member.objects.values("status").annotate(count=Count("id")).order_by("-count")
        )
        by_family = list(
            Member.objects.values("family__name").annotate(count=Count("id")).order_by("-count")
        )
        return Response({
            "total": Member.objects.count(),
            "by_status": by_status,
            "by_family": by_family,
        })
