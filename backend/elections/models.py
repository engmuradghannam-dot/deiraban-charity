from django.db import models
from django.utils import timezone
from members.models import Member


class Election(models.Model):
    """انتخابات (مثلاً: مجلس الإدارة — 7 مقاعد)."""

    title = models.CharField('العنوان', max_length=255)
    description = models.TextField('الوصف', blank=True)
    max_choices = models.PositiveSmallIntegerField(
        'عدد الأصوات المسموح بها', default=1,
        help_text='كم مرشحاً يمكن للعضو اختياره (عدد مقاعد المجلس)'
    )
    starts_at = models.DateTimeField('تبدأ في')
    ends_at = models.DateTimeField('تنتهي في')
    is_active = models.BooleanField('مفعّلة', default=True)
    results_public = models.BooleanField('النتائج علنية', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-starts_at']
        verbose_name = 'انتخابات'
        verbose_name_plural = 'الانتخابات'

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
            return 'ملغاة'
        if now < self.starts_at:
            return 'قادمة'
        if now <= self.ends_at:
            return 'مفتوحة'
        return 'منتهية'


class Candidate(models.Model):
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name='candidates'
    )
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    bio = models.TextField('نبذة', blank=True)
    photo = models.ImageField('صورة', upload_to='candidates/', blank=True)

    class Meta:
        unique_together = ('election', 'member')
        verbose_name = 'مرشح'
        verbose_name_plural = 'المرشحون'

    def __str__(self):
        return f'{self.member.full_name} — {self.election.title}'


class Ballot(models.Model):
    """ورقة اقتراع واحدة — صوت واحد لكل عضو في كل انتخابات."""

    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name='ballots'
    )
    voter = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='ballots')
    candidates = models.ManyToManyField(Candidate, related_name='ballots')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('election', 'voter')
        verbose_name = 'ورقة اقتراع'
        verbose_name_plural = 'أوراق الاقتراع'

    def __str__(self):
        return f'صوت في {self.election.title}'
