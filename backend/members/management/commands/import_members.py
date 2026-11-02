import csv
from django.core.management.base import BaseCommand
from members.models import Member, MembershipFee

YEARS = range(2019, 2026)


class Command(BaseCommand):
    help = 'استيراد الأعضاء من ملف CSV (قالب data/members_import_template.xlsx)'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='مسار ملف CSV')
        parser.add_argument('--approve', action='store_true',
                            help='اعتماد الأعضاء مباشرة')

    def handle(self, *args, **opts):
        created = updated = 0
        with open(opts['file'], encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                name = (row.get('full_name') or '').strip()
                if not name:
                    continue
                defaults = {
                    'full_name': name,
                    'family_name': (row.get('family_name') or '').strip(),
                    'national_id': (row.get('national_id') or '').strip(),
                    'phone': (row.get('phone') or '').strip(),
                    'membership_type': (row.get('membership_type') or 'active').strip(),
                    'status': 'approved' if opts['approve'] else 'pending',
                    'notes': (row.get('notes') or '').strip(),
                }
                num = (row.get('membership_number') or '').strip()
                if num:
                    member, flag = Member.objects.update_or_create(
                        membership_number=num, defaults=defaults
                    )
                else:
                    member = Member.objects.create(**defaults)
                    flag = True
                created, updated = created + flag, updated + (not flag)

                for year in YEARS:
                    val = (row.get(f'fee_{year}') or '').strip()
                    if val:
                        amount = float(val)
                        MembershipFee.objects.update_or_create(
                            member=member, year=year,
                            defaults={
                                'amount': amount,
                                'paid': amount > 0,
                                'paid_at': f'{year}-12-31' if amount > 0 else None,
                            },
                        )
        self.stdout.write(self.style.SUCCESS(
            f'تم الاستيراد: {created} جديد، {updated} محدّث'
        ))
