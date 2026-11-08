import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from membership.models import Family, Member


class Command(BaseCommand):
    help = "استيراد الأعضاء من ملف data/members.csv (يدعم أعمدة y2019_base حتى y2026)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=str(Path(__file__).resolve().parents[4] / "data" / "members.csv"),
            help="مسار ملف CSV",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["file"])
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"الملف غير موجود: {csv_path}"))
            return

        status_map = {
            "عضوفاعل": Member.STATUS_ACTIVE,
            "فاعل": Member.STATUS_ACTIVE,
            "غيرفاعل": Member.STATUS_INACTIVE,
            "غيفاعل": Member.STATUS_INACTIVE,
            "جديد": Member.STATUS_NEW,
            "مسجل": Member.STATUS_REGISTERED,
        }

        created, updated, skipped = 0, 0, 0

        with csv_path.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            with transaction.atomic():
                for row in reader:
                    number = (row.get("number") or "").strip()
                    name = (row.get("name") or "").strip()
                    family_name = (row.get("family") or "").strip()
                    if not number or not name or not family_name:
                        skipped += 1
                        continue

                    family, _ = Family.objects.get_or_create(name=family_name)

                    raw_status = (row.get("status") or "").strip()
                    normalized_status = raw_status.replace(" ", "")
                    status = status_map.get(normalized_status, Member.STATUS_NEW)

                    member, was_created = Member.objects.update_or_create(
                        membership_number=number,
                        defaults={
                            "full_name": name,
                            "family": family,
                            "status": status,
                            "sub_2019_base": (row.get("y2019_base") or "").strip(),
                            "sub_2020": (row.get("y2020") or "").strip(),
                            "sub_2021": (row.get("y2021") or "").strip(),
                            "sub_2022": (row.get("y2022") or "").strip(),
                            "sub_2023": (row.get("y2023") or "").strip(),
                            "sub_2024": (row.get("y2024") or "").strip(),
                            "sub_2025": (row.get("y2025") or "").strip(),
                            "sub_2026": (row.get("y2026") or "").strip(),
                        },
                    )
                    created += int(was_created)
                    updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS(
            f"تم الاستيراد: {created} جديد، {updated} محدَّث، {skipped} متجاهَل (بيانات ناقصة)"
        ))
