# نظام جمعية ديرابان الخيرية

منصة متكاملة للأعضاء: **تسجيل الدخول عبر Google** + **عضويات واشتراكات** + **انتخابات إلكترونية** + **تبرعات**.

## المزايا

| الوحدة | الوصف |
|---|---|
| 🔐 الأعضاء | تسجيل دخول بحساب Google، إكمال بيانات العضوية، اعتماد من الإدارة، سجل اشتراكات 2019–2025 |
| 🗳️ الانتخابات | انتخابات مجلس الإدارة (أي عدد مقاعد)، صوت واحد لكل عضو معتمد، نتائج فورية |
| 💚 التبرعات | حملات تبرع بأهداف ونِسَب إنجاز، تبرع بالاسم أو كزائر، سجل مساهمات العضو |

## التقنيات

- **Backend:** Django 5 + Django REST Framework + dj-rest-auth + django-allauth (Google OAuth) + JWT
- **Frontend:** React 18 + Vite + @react-oauth/google
- قاعدة بيانات SQLite (جاهزة للترقية إلى PostgreSQL)

---

## التشغيل

### 1) Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scriptsctivate
pip install -r requirements.txt
cp .env.example .env                               # عدّل القيم (خاصة Google)
python manage.py migrate
python manage.py seed_admin                        # إنشاء حساب المدير من .env
python manage.py runserver
```

### 2) Frontend

```bash
cd frontend
npm install
cp .env.example .env                             # نفس GOOGLE_CLIENT_ID
npm run dev
```

يفتح على http://localhost:5173 والإدارة على http://127.0.0.1:8000/admin

---

## إعداد Google OAuth (خطوة واحدة إلزامية)

1. افتح https://console.cloud.google.com/apis/credentials
2. أنشئ **OAuth Client ID** من نوع **Web application**
3. أضف في **Authorized redirect URIs**:
   - `http://localhost:5173` (مع نفس القيمة في `GOOGLE_CALLBACK_URL` بملف `.env`)
4. انسخ **Client ID** و **Client Secret** إلى `backend/.env` و `frontend/.env`

> ملاحظة: while developing، يعمل فقط مع الحسابات المضافة كـ Test Users في Google Cloud Console.

---

## استيراد الأعضاء من الكشف القديم

نص ملف الـ PDF المرفوع غير مقروء آليًا (OCR تالف)، لذلك جهّزنا قالباً بنفس الأعمدة:

1. افتح `data/members_import_template.xlsx` وانسخ بيانات الـ 890 عضوًا من الكشف:
   - `membership_number` = رقم العضوية، `full_name`، `family_name`، `national_id`، `phone`
   - `fee_2019` … `fee_2025` = مبلغ كل سنة (اتركه فارغاً إن لم يسدد)
   - `notes` = أي ملاحظة
2. احفظه CSV (‎.csv بترميز UTF-8) ثم:

```bash
python manage.py import_members --file members.csv --approve
```

> ⚠️ **خصوصية:** الكشف يحتوي أرقاماً وطنية وهواتف — لا ترفعه على GitHub ولا تشاركه. الملفات الشخصية تبقى على جهازك فقط.

## دورة العمل اليومية

1. عضو جديد يسجل عبر Google → يكمل بياناته → **بانتظار الموافقة**
2. الإدارة تفتح Django Admin → الأعضاء → تطابق الاسم مع الكشف → action **"اعتماد وإصدار رقم عضوية"**
3. إنشاء انتخابات: Admin → Elections → أضف المرشحين وحدد عدد المقاعد ووقت التصويت
4. التبرعات: Admin → Donations يسجل النقدي/البنكي، والإلكتروني يُربط ببوابة دفع لاحقاً

## الخطوات التالية المقترحة

- بوابة دفع إلكتروني (HyperPay / Tap / Stripe) لخيار "دفع إلكتروني"
- إشعارات SMS/WhatsApp للتذكير بالانتخابات والاشتراكات
- تقارير PDF/Excel (كشف الهيئة العامة مثل النموذج الأصلي)
- PostgreSQL + Docker للنشر
