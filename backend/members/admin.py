from django.contrib import admin
from .models import Member, MembershipFee


class MembershipFeeInline(admin.TabularInline):
    model = MembershipFee
    extra = 0


@admin.action(description='اعتماد الأعضاء المحددين وإصدار رقم عضوية')
def approve_members(modeladmin, request, queryset):
    for member in queryset.filter(status=Member.Status.PENDING):
        if not member.membership_number:
            member.membership_number = next_membership_number()
        member.status = Member.Status.APPROVED
        member.save(update_fields=['membership_number', 'status'])


def next_membership_number():
    nums = []
    for v in Member.objects.exclude(membership_number__isnull=True).exclude(
            membership_number='').values_list('membership_number', flat=True):
        if str(v).isdigit():
            nums.append(int(v))
    return str(max(nums, default=6000) + 1)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['membership_number', 'full_name', 'family_name',
                    'membership_type', 'status', 'phone', 'user']
    list_filter = ['status', 'membership_type', 'family_name']
    search_fields = ['full_name', 'family_name', 'membership_number',
                     'national_id', 'phone']
    actions = [approve_members]
    inlines = [MembershipFeeInline]
