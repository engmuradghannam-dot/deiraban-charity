from django.contrib import admin

from members.models import Member
from .models import Candidate, Election, VoterParticipation


class CandidateInline(admin.TabularInline):
    model = Candidate
    raw_id_fields = ["member"]
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "member":
            kwargs["queryset"] = Member.objects.filter(
                status=Member.Status.APPROVED,
                membership_type=Member.Type.ACTIVE,
                registry_member__status="عضو فاعل",
            ).select_related("registry_member")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ["title", "starts_at", "ends_at", "is_active", "max_choices", "results_public"]
    list_filter = ["is_active", "results_public"]
    search_fields = ["title"]
    inlines = [CandidateInline]


@admin.register(VoterParticipation)
class VoterParticipationAdmin(admin.ModelAdmin):
    # لا تعرض هوية العضو؛ يظهر سجل المشاركة ووقتها فقط.
    list_display = ["election", "submitted_at"]
    list_filter = ["election"]
    readonly_fields = ["election", "submitted_at"]
    fields = ["election", "submitted_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
