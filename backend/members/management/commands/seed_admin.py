import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'إنشاء حساب المدير (superuser) من متغيرات البيئة'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.getenv('ADMIN_USERNAME', 'admin')
        email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        password = os.getenv('ADMIN_PASSWORD', 'Admin@12345')
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username, email=email, password=password
            )
            self.stdout.write(self.style.SUCCESS(f'تم إنشاء المدير: {username}'))
        else:
            self.stdout.write('حساب المدير موجود مسبقاً.')
