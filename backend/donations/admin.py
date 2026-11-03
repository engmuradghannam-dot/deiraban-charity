from django.contrib import admin
from .models import DonationCampaign, Donation


@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    list_display = ['title', 'goal_amount', 'is_active', 'created_at']
    list_filter = ['is_active']


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['donor_name', 'campaign', 'amount', 'currency',
                    'method', 'status', 'created_at']
    list_filter = ['status', 'method', 'currency', 'campaign']
    search_fields = ['donor_name', 'donor_phone']
