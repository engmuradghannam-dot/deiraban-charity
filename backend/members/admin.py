from django.contrib import admin, messages

from .models import Member, MembershipFee


class MembershipFeeInline(admin.TabularInline):
    model = MembershipFee
    extra = 0


@admin.action(description="اعتماد الطلبات المحددة المرتبطة بسجل رسمي")
def approve_members(modeladmin, request, queryset):
    pending = queryset.filter(status=Member.Status.PENDING)
    linked = pending.filter(registry_member__isnull=False)
    updated = linked.update(status=Member.Status.APPROVED)
    skipped = pending.count() - updated
    modeladmin.message_user(request, f"تم اعتماد {updated} طلب عضوية.", messages.SUCCESS)
    if skipped:
        modeladmin.message_user(
            request,
            f"لم يتم اعتماد {skipped} طلباً لعدم ربطه بسجل العضوية الرسمي.",
            messages.WARNING,
        )


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = [
        "membership_number", "full_name", "family_name", "membership_type", "status", "phone", "user"
    ]
    list_filter = ["status", "membership_type", "family_name"]
    search_fields = [
        "full_name", "family_name", "membership_number", "registry_member__membership_number", "phone"
    ]
    list_select_related = ["registry_member", "user"]
    raw_id_fields = ["registry_member", "user"]
    actions = [approve_members]
    inlines = [MembershipFeeInline]

    def save_model(self, request, obj, form, change):
        if obj.registry_member_id:
            registry = obj.registry_member
            obj.membership_number = registry.membership_number
            obj.membership_type = (
                Member.Type.ACTIVE
                if registry.status == registry.STATUS_ACTIVE
                else Member.Type.INACTIVE
            )
        super().save_model(request, obj, form, change)
