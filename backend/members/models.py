from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Member(models.Model):
    """عضو الجمعية — يرتبط بحساب Google الخاص به."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'بانتظار الموافقة'
        APPROVED = 'approved', 'عضو معتمد'
        REJECTED = 'rejected', 'مرفوض'

    class Type(models.TextChoices):
        ACTIVE = 'active', 'عضو فاعل'
        INACTIVE = 'inactive', 'غير فاعل'

    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='member_profile', verbose_name='حساب المستخدم'
    )
    membership_number = models.CharField(
        'رقم العضوية', max_length=20, unique=True, null=True, blank=True
    )
    full_name = models.CharField('الاسم الرباعي', max_length=255)
    family_name = models.CharField('اسم العائلة', max_length=100, db_index=True)
    national_id = models.CharField('الرقم الوطني', max_length=20, blank=True)
    phone = models.CharField('رقم الهاتف', max_length=20, blank=True)
    membership_type = models.CharField(
        'صفة العضوية', max_length=10, choices=Type.choices, default=Type.ACTIVE
    )
    status = models.CharField(
        'الحالة', max_length=10, choices=Status.choices, default=Status.PENDING
    )
    notes = models.TextField('ملاحظات', blank=True)
    created_at = models.DateTimeField('تاريخ التسجيل', auto_now_add=True)

    class Meta:
        ordering = ['family_name', 'full_name']
        verbose_name = 'عضو'
        verbose_name_plural = 'الأعضاء'

    def __str__(self):
        return f'{self.full_name} ({self.membership_number or "بدون رقم"})'


class MembershipFee(models.Model):
    """اشتراك سنوي لعضو (مثل أعمدة 2019-2025 في الكشف)."""

    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name='fees', verbose_name='العضو'
    )
    year = models.PositiveIntegerField('السنة')
    amount = models.DecimalField('المبلغ', max_digits=8, decimal_places=2, default=0)
    paid = models.BooleanField('مدفوع', default=False)
    paid_at = models.DateField('تاريخ الدفع', null=True, blank=True)

    class Meta:
        unique_together = ('member', 'year')
        ordering = ['year']
        verbose_name = 'اشتراك سنوي'
        verbose_name_plural = 'الاشتراكات السنوية'

    def __str__(self):
        return f'{self.member.full_name} — {self.year}'
