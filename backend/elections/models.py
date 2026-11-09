from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from members.models import Member


class Election(models.Model):
    """انتخابات الجمعية ومواعيد فتحها وإغلاقها."""

    title = models.CharField("العنوان", max_length=255)
    description = models.TextField("الوصف", blank=True)
    max_choices = models.PositiveSmallIntegerField(
        "عدد الأصوات المسموح بها",
        default=1,
        validators=[MinValueValidator(1)],
        help_text="أقصى عدد من المرشحين الذين يمكن للعضو اختيارهم.",
    )
    starts_at = models.DateTimeField("تبدأ في")
    ends_at = models.DateTimeField("تنتهي في")
    is_active = models.BooleanField("مفعّلة", default=True)
    results_public = models.BooleanField("النتائج علنية", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-starts_at"]
        verbose_name = "انتخابات"
        verbose_name_plural = "الانتخابات"

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            from django.core.exceptions import ValidationError

            raise ValidationError({"ends_at": "يجب أن يكون وقت الإغلاق بعد وقت البدء."})

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        now = timezone.now()
        return self.is_active and self.starts_at <= now <= self.ends_at

    @property
    def status_label(self):
        now = timezone.now()
        if not self.is_active:
            return "ملغاة"
        if now < self.starts_at:
            return "قادمة"
        if now <= self.ends_at:
            return "مفتوحة"
        return "منتهية"


class Candidate(models.Model):
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="candidates", verbose_name="الانتخابات"
    )
    member = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="candidacies", verbose_name="العضو المرشح"
    )
    bio = models.TextField("نبذة", blank=True)
    photo = models.ImageField("صورة", upload_to="candidates/", blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["election", "member"], name="unique_election_candidate")
        ]
        verbose_name = "مرشح"
        verbose_name_plural = "المرشحون"

    def __str__(self):
        return f"{self.member.full_name} — {self.election.title}"


class VoterParticipation(models.Model):
    """سجل تحقق من المشاركة لا يحتوي على مرجع إلى ورقة الاقتراع."""

    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="participations", verbose_name="الانتخابات"
    )
    voter = models.ForeignKey(
        Member, on_delete=models.PROTECT, related_name="election_participations", verbose_name="العضو"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["election", "voter"], name="one_participation_per_election")
        ]
        ordering = ["-submitted_at"]
        verbose_name = "تسجيل مشاركة انتخابية"
        verbose_name_plural = "سجلات المشاركة الانتخابية"

    def __str__(self):
        return f"مشاركة مسجلة — {self.election.title}"


class Ballot(models.Model):
    """ورقة اقتراع منفصلة عن هوية صاحبها؛ تعرض النتائج كمجاميع فقط."""

    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name="ballots", verbose_name="الانتخابات"
    )
    candidates = models.ManyToManyField(Candidate, related_name="ballots", verbose_name="الاختيارات")

    class Meta:
        verbose_name = "ورقة اقتراع"
        verbose_name_plural = "أوراق الاقتراع"

    def __str__(self):
        return f"ورقة اقتراع — {self.election.title}"
