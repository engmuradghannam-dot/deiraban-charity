from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Member(models.Model):
    """حساب عضو موثّق ومربوط بسجل الجمعية المستورد."""

    class Status(models.TextChoices):
        PENDING = "pending", "بانتظار الموافقة"
        APPROVED = "approved", "عضو معتمد"
        REJECTED = "rejected", "مرفوض"

    class Type(models.TextChoices):
        ACTIVE = "active", "عضو فاعل"
        INACTIVE = "inactive", "غير فاعل"

    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="member_profile", verbose_name="حساب المستخدم",
    )
    registry_member = models.OneToOneField(
        "membership.Member", on_delete=models.PROTECT, null=True, blank=True,
        related_name="account_profile", verbose_name="سجل العضوية الرسمي",
    )
    membership_number = models.CharField(
        "رقم العضوية", max_length=20, unique=True, null=True, blank=True
    )
    full_name = models.CharField("الاسم الرباعي", max_length=255)
    family_name = models.CharField("اسم العائلة", max_length=100, db_index=True)
    national_id = models.CharField("الرقم الوطني", max_length=20, blank=True)
    phone = models.CharField("رقم الهاتف", max_length=20, blank=True)
    phone_secondary = models.CharField("رقم هاتف إضافي", max_length=20, blank=True)
    profile_photo = models.ImageField("الصورة الشخصية", upload_to="member_profiles/", blank=True)
    id_scan = models.FileField("صورة الهوية", upload_to="member_documents/", blank=True)
    family_book_scan = models.FileField("صورة دفتر العائلة", upload_to="member_documents/", blank=True)
    membership_type = models.CharField(
        "صفة العضوية", max_length=10, choices=Type.choices, default=Type.INACTIVE
    )
    status = models.CharField(
        "الحالة", max_length=10, choices=Status.choices, default=Status.PENDING
    )
    notes = models.TextField("ملاحظات", blank=True)
    created_at = models.DateTimeField("تاريخ التسجيل", auto_now_add=True)

    class Meta:
        ordering = ["family_name", "full_name"]
        verbose_name = "عضو"
        verbose_name_plural = "الأعضاء"

    def __str__(self):
        return f"{self.full_name} ({self.membership_number or 'بدون رقم'})"

    @property
    def is_eligible_to_vote(self):
        registry = self.registry_member
        return bool(
            self.status == self.Status.APPROVED
            and self.membership_type == self.Type.ACTIVE
            and registry
            and registry.status == registry.STATUS_ACTIVE
        )


class MembershipFee(models.Model):
    """اشتراك سنوي مرتبط بملف العضو في المنصة."""

    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="fees", verbose_name="العضو"
    )
    year = models.PositiveIntegerField("السنة")
    amount = models.DecimalField("المبلغ", max_digits=8, decimal_places=2, default=0)
    paid = models.BooleanField("مدفوع", default=False)
    paid_at = models.DateField("تاريخ الدفع", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["member", "year"], name="unique_member_fee_year")
        ]
        ordering = ["year"]
        verbose_name = "اشتراك سنوي"
        verbose_name_plural = "الاشتراكات السنوية"

    def __str__(self):
        return f"{self.member.full_name} — {self.year}"
