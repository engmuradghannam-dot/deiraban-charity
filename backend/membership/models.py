from django.db import models


class Family(models.Model):
    """اسم العائلة (حمولة) داخل الجمعية"""

    name = models.CharField(max_length=150, unique=True, verbose_name="اسم العائلة")

    class Meta:
        verbose_name = "عائلة"
        verbose_name_plural = "العائلات"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Member(models.Model):
    STATUS_ACTIVE = "عضو فاعل"
    STATUS_INACTIVE = "غير فاعل"
    STATUS_NEW = "جديد"
    STATUS_REGISTERED = "مسجل"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "عضو فاعل"),
        (STATUS_INACTIVE, "غير فاعل"),
        (STATUS_NEW, "جديد"),
        (STATUS_REGISTERED, "مسجل"),
    ]

    membership_number = models.CharField(
        max_length=20, unique=True, verbose_name="رقم العضوية"
    )
    full_name = models.CharField(max_length=255, verbose_name="الاسم الكامل")
    family = models.ForeignKey(
        Family, on_delete=models.PROTECT, related_name="members", verbose_name="العائلة"
    )
    national_id = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="الرقم الوطني"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name="حالة العضوية"
    )
    notes = models.TextField(blank=True, verbose_name="ملاحظات")

    # سجل الاشتراكات السنوي — تطابق كشف الجمعية الأصلي (قيمة الإيصال أو "/" أو حالة مثل "مسجل")
    sub_2019_base = models.CharField(max_length=20, blank=True, default="")
    sub_2020 = models.CharField(max_length=20, blank=True, default="")
    sub_2021 = models.CharField(max_length=20, blank=True, default="")
    sub_2022 = models.CharField(max_length=20, blank=True, default="")
    sub_2023 = models.CharField(max_length=20, blank=True, default="")
    sub_2024 = models.CharField(max_length=20, blank=True, default="")
    sub_2025 = models.CharField(max_length=20, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "عضو"
        verbose_name_plural = "الأعضاء"
        ordering = ["membership_number"]

    def __str__(self):
        return f"{self.membership_number} - {self.full_name}"

    @property
    def subscriptions(self):
        return {
            "2019_base": self.sub_2019_base,
            "2020": self.sub_2020,
            "2021": self.sub_2021,
            "2022": self.sub_2022,
            "2023": self.sub_2023,
            "2024": self.sub_2024,
            "2025": self.sub_2025,
        }
