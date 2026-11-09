from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from sheets_storage import SheetsRepository, sheets_enabled
from .models import Donation, DonationCampaign
from .serializers import CampaignSerializer, DonationCreateSerializer, MyDonationSerializer


def _repo():
    return SheetsRepository()


class CampaignListView(generics.ListAPIView):
    serializer_class = CampaignSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        if sheets_enabled():
            return Response(_repo().campaigns())
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return DonationCampaign.objects.filter(is_active=True)


class DonationCreateView(generics.CreateAPIView):
    serializer_class = DonationCreateSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def create(self, request, *args, **kwargs):
        if not sheets_enabled():
            return super().create(request, *args, **kwargs)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        member = getattr(user, "member_profile", None) if user else None
        donor_name = serializer.validated_data.get("donor_name", "").strip()
        if not donor_name and member:
            donor_name = member.full_name
        if not donor_name and user:
            donor_name = user.get_full_name().strip() or user.email or user.get_username()
        campaign = serializer.validated_data.get("campaign")
        data = {key: value for key, value in serializer.validated_data.items() if key != "campaign"}
        data.update({"campaign_id": str(campaign.pk) if campaign else "", "member_id": str(member.pk) if member else "", "user_id": str(user.pk) if user else "", "donor_name": donor_name, "currency": "JOD", "status": Donation.Status.PENDING})
        return Response(_repo().create_donation(data), status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        request = self.request
        user = request.user if request.user.is_authenticated else None
        member = getattr(user, "member_profile", None) if user else None
        donor_name = serializer.validated_data.get("donor_name", "").strip()
        if not donor_name and member:
            donor_name = member.full_name
        if not donor_name and user:
            donor_name = user.get_full_name().strip() or user.email or user.get_username()
        serializer.save(member=member, user=user, donor_name=donor_name, status=Donation.Status.PENDING, currency="JOD")


class MyDonationsView(generics.ListAPIView):
    serializer_class = MyDonationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        if sheets_enabled():
            member = getattr(request.user, "member_profile", None)
            return Response(_repo().donations_for_user(request.user.pk, member.pk if member else None))
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        member = getattr(self.request.user, "member_profile", None)
        query = Q(user=self.request.user)
        if member:
            query |= Q(member=member)
        return Donation.objects.filter(query).select_related("campaign").distinct()
