from rest_framework import generics, permissions
from .models import DonationCampaign, Donation
from .serializers import (CampaignSerializer, DonationCreateSerializer,
                          MyDonationSerializer)


class CampaignListView(generics.ListAPIView):
    """حملات التبرع المفعّلة (متاحة للجميع)."""
    serializer_class = CampaignSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return DonationCampaign.objects.filter(is_active=True)


class DonationCreateView(generics.CreateAPIView):
    """تسجيل تبرع — العضو مسجل باسمه، والزائر يكتب اسمه."""
    serializer_class = DonationCreateSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        request = self.request
        member = (getattr(request.user, 'member_profile', None)
                  if request.user.is_authenticated else None)
        is_online = serializer.validated_data.get('method') == 'online'
        if member and not serializer.validated_data.get('donor_name'):
            serializer.save(member=member,
                            status='pending' if is_online else 'completed')
        else:
            serializer.save(member=member,
                            status='pending' if is_online else 'completed')


class MyDonationsView(generics.ListAPIView):
    serializer_class = MyDonationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        member = getattr(self.request.user, 'member_profile', None)
        if not member:
            return Donation.objects.none()
        return Donation.objects.filter(member=member)
