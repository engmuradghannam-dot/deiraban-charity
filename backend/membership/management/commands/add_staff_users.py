"""
أمر لإضافة دفعة من حسابات المسؤولين (محررين) دفعة وحدة عبر قائمة إيميلات.

الاستخدام:
  python manage.py add_staff_users --emails user1@example.com user2@example.com
  أو من ملف نصي (إيميل بكل سطر):
  python manage.py add_staff_users --file emails.txt

كل حساب يُنشأ بصلاحية "staff" (يقدر يدخل لوحة /admin/ ويعدّل الأعضاء ويضيف جدد)
لكن بدون صلاحية "superuser" الكاملة (ما يقدر يحذف حسابات مسؤولين ثانين أو يغيّر إعدادات حساسة).

كلمة المرور تُولَّد تلقائياً وتُطبع لك هنا مرة وحدة فقط — انسخها وأرسلها للشخص المعني
بطريقة آمنة (مو إيميل عادي غير مشفر لو ممكن)، لأنها ما تُحفظ ولا تُعرض مرة ثانية.
"""
import secrets
import string
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "إضافة مجموعة إيميلات كحسابات مسؤولين (staff) يقدرون يدخلون لوحة الإدارة"

    def add_arguments(self, parser):
        parser.add_argument(
            "--emails", nargs="+", help="قائمة إيميلات مفصولة بمسافة"
        )
        parser.add_argument(
            "--file", type=str, help="مسار ملف نصي فيه إيميل بكل سطر"
        )

    def handle(self, *args, **options):
        emails = list(options.get("emails") or [])

        file_path = options.get("file")
        if file_path:
            path = Path(file_path)
            if not path.exists():
                raise CommandError(f"الملف غير موجود: {path}")
            with path.open(encoding="utf-8") as f:
                emails += [line.strip() for line in f if line.strip()]

        if not emails:
            raise CommandError("لازم تمرر إيميلات عبر --emails أو --file")

        created, skipped = 0, 0
        for email in emails:
            email = email.strip().lower()
            if not email or "@" not in email:
                self.stdout.write(self.style.WARNING(f"تجاهلت قيمة غير صالحة: {email!r}"))
                continue

            if User.objects.filter(username=email).exists():
                self.stdout.write(self.style.WARNING(f"موجود مسبقاً، تم التجاوز: {email}"))
                skipped += 1
                continue

            password = generate_password()
            User.objects.create_user(
                username=email,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=False,
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(
                f"تم إنشاء حساب: {email}  |  كلمة المرور المؤقتة: {password}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"\nالخلاصة: {created} حساب جديد، {skipped} تم تجاوزه (موجود مسبقاً)"
        ))
        self.stdout.write(
            "كل حساب يقدر يدخل على /admin/ بنفس الإيميل ككلمة مستخدم وكلمة المرور المؤقتة أعلاه. "
            "ينصح يغيّرها أول ما يدخل من: Admin → تغيير كلمة المرور."
        )
