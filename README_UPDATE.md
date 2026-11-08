# تحديث شامل: دمج الكشف الجديد (2025/2026) + ميزات الأدمن

## وش تغيّر

**البيانات (data/members.csv):**
- دمجت كشف الأعضاء الجديد (75 صفحة، 2268 سجل) مع بياناتك الحالية
- **722 عضو** تحدّثت بياناتهم من الكشف الجديد (أسماء، حالة، اشتراكات حتى 2026)
- **1546 عضو جديد** أُضيفوا (رقم عضويتهم يبدأ بـ "S" لتمييزهم، مثل S523) — حالتهم مبدئياً "جديد" لأن الكشف الأصلي ما حدد حالتهم، راجعها من الأدمن
- عدد الأسماء المشكوك فيها (مقطوعة/ملتصقة) نزل من **111 إلى 26 فقط** (ملف `suspicious_rows_v2.csv` المرفق فيه القائمة الكاملة للمراجعة اليدوية)
- **إجمالي الأعضاء بعد الدمج: 2433**

**الكود:**
- `backend/membership/models.py` — أضفت حقل `sub_2026` (اشتراك سنة 2026)
- `backend/membership/migrations/0002_member_sub_2026.py` — migration جديدة لإضافة العمود بقاعدة البيانات
- `backend/membership/serializers.py` — يعرض حقل 2026 بالـ API
- `backend/membership/admin.py` — إضافة حقل 2026 بنموذج التعديل + تعديل الحالة مباشرة من القائمة
- `backend/membership/management/commands/import_members.py` — يدعم قراءة عمود y2026 من الملف
- `backend/membership/management/commands/add_staff_users.py` — أمر إضافة مجموعة إيميلات كمسؤولين (من الطلب السابق)

## خطوات التطبيق

انسخ كل الملفات التالية فوق نظيراتها في `C:\deraban_project` (استبدال):

```
backend/membership/models.py
backend/membership/admin.py
backend/membership/serializers.py
backend/membership/migrations/0002_member_sub_2026.py   (ملف جديد)
backend/membership/management/commands/import_members.py
backend/membership/management/commands/add_staff_users.py   (ملف جديد، لو ما نسخته قبل)
data/members.csv   (استبدال كامل — هذا هو الملف المدموج)
```

ثم:
```
cd C:\deraban_project
git add -A
git commit -m "feat: دمج كشف 2025/2026 + دعم اشتراك 2026 + تحسينات الأدمن"
git push
```

Render بيعيد النشر تلقائياً، ويشغّل `migrate` (يضيف عمود 2026) ثم `import_members` (يحدّث/يضيف 2433 عضو).

## ⚠️ مهم — راجع بنفسك

- **26 اسم** لسا فيهم احتمال خطأ استخراج (ملف `suspicious_rows_v2.csv`) — صحّحهم من لوحة Django Admin بعد النشر
- **1546 عضو جديد** حالتهم "جديد" افتراضياً — راجعهم وحدّث حالتهم الفعلية (فاعل/غير فاعل) من الكشف الأصلي إذا متوفر
- بعض الأعضاء الجدد قد يكونوا نفس الشخص مسجل مرتين بصيغة مختلفة قليلاً (الكشف الجديد ما كان فيه رقم ربط واضح لكل الحالات) — يُفضّل مراجعة سريعة لأسماء العائلات الكبيرة للتأكد من عدم وجود تكرار
