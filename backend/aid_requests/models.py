from django.db import models


class AidRequest(models.Model):
    """طلب مساعدة مقدَّم من شخص محتاج عبر تسجيل الدخول بحساب Google.

    منفصل تماماً عن تطبيق membership (سجل الأعضاء المشتركين) وعن تطبيق
    members (حسابات الأعضاء الموثّقين) — هذا لأي شخص من خارج سجل الأعضاء
    يحتاج مساعدة من الجمعية.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "قيد المراجعة"
        APPROVED = "approved", "مقبول"
        REJECTED = "rejected", "مرفوض"

    google_sub = models.CharField("معرّف جوجل", max_length=255, unique=True)
    email = models.EmailField("البريد الإلكتروني")
    full_name = models.CharField("الاسم الكامل", max_length=255)
    family_name = models.CharField("اسم العائلة", max_length=150, blank=True)
    phone = models.CharField("رقم الجوال", max_length=30, blank=True)
    national_id = models.CharField("الرقم الوطني", max_length=20, blank=True)
    address = models.CharField("العنوان", max_length=255, blank=True)
    need_description = models.TextField("وصف الحالة / المساعدة المطلوبة", blank=True)
    status = models.CharField(
        "حالة الطلب", max_length=20, choices=Status.choices, default=Status.PENDING
    )
    reviewer_notes = models.TextField("ملاحظات المراجعة", blank=True)
    created_at = models.DateTimeField("تاريخ التقديم", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "طلب مساعدة"
        verbose_name_plural = "طلبات المساعدة"

    def __str__(self):
        return f"{self.full_name} ({self.get_status_display()})"
