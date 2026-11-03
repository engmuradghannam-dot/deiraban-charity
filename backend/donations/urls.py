from django.urls import path
from .views import CampaignListView, DonationCreateView, MyDonationsView

urlpatterns = [
    path('campaigns/', CampaignListView.as_view(), name='campaign-list'),
    path('', DonationCreateView.as_view(), name='donation-create'),
    path('mine/', MyDonationsView.as_view(), name='my-donations'),
]
