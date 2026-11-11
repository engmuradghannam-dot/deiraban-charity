from django.contrib import admin

from .models import AidRequest


@admin.register(AidRequest)
class AidRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "family_name", "phone", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status",)
    search_fields = ("full_name", "family_name", "phone", "national_id", "email")
    readonly_fields = ("google_sub", "email", "created_at", "updated_at")
    fieldsets = (
        ("بيانات مقدّم الطلب", {"fields": ("full_name", "family_name", "phone", "national_id", "address")}),
        ("الطلب", {"fields": ("need_description",)}),
        ("المراجعة", {"fields": ("status", "reviewer_notes")}),
        ("حساب جوجل", {"fields": ("google_sub", "email")}),
        ("تواريخ", {"fields": ("created_at", "updated_at")}),
    )
