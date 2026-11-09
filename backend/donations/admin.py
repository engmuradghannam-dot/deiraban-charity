from django.contrib import admin, messages

from .models import Donation, DonationCampaign


@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    list_display = ["title", "goal_amount", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["title"]


@admin.action(description="تأكيد قبض التبرعات المحددة")
def mark_as_completed(modeladmin, request, queryset):
    updated = queryset.filter(status=Donation.Status.PENDING).update(status=Donation.Status.COMPLETED)
    modeladmin.message_user(request, f"تم تأكيد {updated} تبرعاً قيد المراجعة.", messages.SUCCESS)


@admin.action(description="تعليم التبرعات المحددة كغير مكتملة")
def mark_as_failed(modeladmin, request, queryset):
    updated = queryset.filter(status=Donation.Status.PENDING).update(status=Donation.Status.FAILED)
    modeladmin.message_user(request, f"تم تحديث حالة {updated} تبرعاً.", messages.WARNING)


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ["id", "donor_name", "campaign", "amount", "currency", "method", "status", "created_at"]
    list_filter = ["status", "method", "currency", "campaign"]
    search_fields = ["donor_name", "donor_phone", "notes"]
    readonly_fields = ["currency", "created_at"]
    actions = [mark_as_completed, mark_as_failed]
