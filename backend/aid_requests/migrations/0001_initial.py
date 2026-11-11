from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AidRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("google_sub", models.CharField(max_length=255, unique=True, verbose_name="معرّف جوجل")),
                ("email", models.EmailField(max_length=254, verbose_name="البريد الإلكتروني")),
                ("full_name", models.CharField(max_length=255, verbose_name="الاسم الكامل")),
                ("family_name", models.CharField(blank=True, max_length=150, verbose_name="اسم العائلة")),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="رقم الجوال")),
                ("national_id", models.CharField(blank=True, max_length=20, verbose_name="الرقم الوطني")),
                ("address", models.CharField(blank=True, max_length=255, verbose_name="العنوان")),
                ("need_description", models.TextField(blank=True, verbose_name="وصف الحالة / المساعدة المطلوبة")),
                ("status", models.CharField(
                    choices=[("pending", "قيد المراجعة"), ("approved", "مقبول"), ("rejected", "مرفوض")],
                    default="pending", max_length=20, verbose_name="حالة الطلب",
                )),
                ("reviewer_notes", models.TextField(blank=True, verbose_name="ملاحظات المراجعة")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التقديم")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")),
            ],
            options={
                "verbose_name": "طلب مساعدة",
                "verbose_name_plural": "طلبات المساعدة",
                "ordering": ["-created_at"],
            },
        ),
    ]
