from django.db import models
from django.db.models import Sum
from members.models import Member


class DonationCampaign(models.Model):
    """حملة تبرع (زكوات، كفالات، مشاريع...)."""

    title = models.CharField('العنوان', max_length=255)
    description = models.TextField('الوصف', blank=True)
    goal_amount = models.DecimalField(
        'الهدف', max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_active = models.BooleanField('مفعّلة', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'حملة تبرع'
        verbose_name_plural = 'حملات التبرع'

    def __str__(self):
        return self.title

    @property
    def collected(self):
        total = self.donations.filter(status='completed').aggregate(
            s=Sum('amount'))['s']
        return total or 0


class Donation(models.Model):
    class Method(models.TextChoices):
        ONLINE = 'online', 'دفع إلكتروني'
        CASH = 'cash', 'نقدي'
        BANK = 'bank', 'حوالة بنكية'

    class Status(models.TextChoices):
        PENDING = 'pending', 'بانتظار الدفع'
        COMPLETED = 'completed', 'مكتمل'
        FAILED = 'failed', 'فاشل'
        REFUNDED = 'refunded', 'مسترجع'

    campaign = models.ForeignKey(
        DonationCampaign, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='donations', verbose_name='الحملة'
    )
    member = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='donations', verbose_name='العضو (إن وجد)'
    )
    donor_name = models.CharField('اسم المتبرع', max_length=255)
    donor_phone = models.CharField('هاتف المتبرع', max_length=20, blank=True)
    amount = models.DecimalField('المبلغ', max_digits=10, decimal_places=2)
    currency = models.CharField('العملة', max_length=3, default='JOD')
    method = models.CharField('طريقة الدفع', max_length=10, choices=Method.choices)
    status = models.CharField('الحالة', max_length=10, choices=Status.choices,
                              default=Status.PENDING)
    notes = models.CharField('ملاحظات', max_length=255, blank=True)
    created_at = models.DateTimeField('تاريخ التبرع', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تبرع'
        verbose_name_plural = 'التبرعات'

    def __str__(self):
        return f'{self.donor_name} — {self.amount} {self.currency}'
