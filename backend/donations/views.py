from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from .models import Donation, DonationCampaign
from .serializers import CampaignSerializer, DonationCreateSerializer, MyDonationSerializer


class CampaignListView(generics.ListAPIView):
    """الحملات النشطة للعرض العام."""

    serializer_class = CampaignSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return DonationCampaign.objects.filter(is_active=True)


class DonationCreateView(generics.CreateAPIView):
    """تسجيل نية التبرع؛ لا يتم تأكيد القبض إلا بواسطة الإدارة."""

    serializer_class = DonationCreateSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def perform_create(self, serializer):
        request = self.request
        user = request.user if request.user.is_authenticated else None
        member = getattr(user, "member_profile", None) if user else None
        donor_name = serializer.validated_data.get("donor_name", "").strip()
        if not donor_name and member:
            donor_name = member.full_name
        if not donor_name and user:
            donor_name = user.get_full_name().strip() or user.email or user.get_username()
        serializer.save(
            member=member,
            user=user,
            donor_name=donor_name,
            status=Donation.Status.PENDING,
            currency="JOD",
        )


class MyDonationsView(generics.ListAPIView):
    serializer_class = MyDonationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        member = getattr(self.request.user, "member_profile", None)
        query = Q(user=self.request.user)
        if member:
            query |= Q(member=member)
        return Donation.objects.filter(query).select_related("campaign").distinct()
