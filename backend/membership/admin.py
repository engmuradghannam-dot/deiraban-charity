from django.contrib import admin
from .models import Family, Member


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ("name", "member_count")
    search_fields = ("name",)

    def member_count(self, obj):
        return obj.members.count()

    member_count.short_description = "عدد الأعضاء"


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "membership_number",
        "full_name",
        "family",
        "status",
        "sub_2025",
        "sub_2024",
    )
    list_editable = ("status",)  # تعديل الحالة مباشرة من قائمة الأعضاء بدون فتح كل سجل
    list_filter = ("status", "family")
    search_fields = ("full_name", "membership_number", "national_id")
    autocomplete_fields = ("family",)
    list_per_page = 50
    fieldsets = (
        ("بيانات العضو", {
            "fields": ("membership_number", "full_name", "family", "national_id", "status", "notes")
        }),
        ("سجل الاشتراكات السنوي", {
            "fields": (
                "sub_2019_base", "sub_2020", "sub_2021",
                "sub_2022", "sub_2023", "sub_2024", "sub_2025", "sub_2026",
            )
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # رقم العضوية لا يُعدَّل بعد إنشائه (منعاً لتعارض الأرقام)، لكن يبقى قابلاً للتحديد عند الإضافة
        if obj:
            return ("membership_number",)
        return ()
