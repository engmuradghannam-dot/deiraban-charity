# إعداد النشر على Render

يُهيّئ `render.yaml` خدمتي Django وReact. قبل التشغيل الفعلي، راجع الخطوات التالية؛ المنصة لا تنشئ حساب Google OAuth أو قاعدة بيانات دائمة تلقائياً.

## 1. ربط المستودع

من لوحة Render اختر **New + → Blueprint** ثم اربط مستودع `deiraban-charity`. يستخدم الـ Blueprint `config.wsgi:application` وتُشغّل الترحيلات واستيراد سجل الأعضاء أثناء البناء.

## 2. إعداد قاعدة بيانات دائمة

أنشئ PostgreSQL أو استخدم قاعدة دائمة لديك، ثم ضع رابطها في `DATABASE_URL` لخدمة الخلفية. لا تستخدم SQLite على نظام ملفات Render المؤقت لحفظ أوراق التصويت وسجلات التبرع.

## 3. إعداد Google OAuth والربط بين الخدمتين

اضبط المتغيرات الآتية في لوحة Render:

- الخلفية: `DJANGO_SECRET_KEY`، `GOOGLE_CLIENT_ID`، `GOOGLE_CLIENT_SECRET`، `GOOGLE_CALLBACK_URL`، و`CORS_ALLOWED_ORIGINS`.
- الواجهة: `VITE_API_URL` على صورة `https://<backend-host>.onrender.com/api`، و`VITE_GOOGLE_CLIENT_ID`.

أضف نطاق الواجهة إلى Authorized JavaScript origins في Google Cloud Console، واستخدم نطاق الواجهة نفسه في `GOOGLE_CALLBACK_URL` و`CORS_ALLOWED_ORIGINS` بحسب إعداد Google OAuth. لا تضع أسرار Google في مستودع Git.

عند استخدام زر `@react-oauth/google` الحالي بنمط popup و`auth-code`، يجب أن تكون قيمة `GOOGLE_CALLBACK_URL` في Render هي `postmessage`، بينما تكون قيمة `CORS_ALLOWED_ORIGINS` هي `https://deraban-frontend.onrender.com`، ويُضاف النطاق نفسه إلى Authorized JavaScript origins في Google Cloud Console.

## 4. تخزين الدومين في Google Sheets (اختياري)

يمكن تفعيل مستودع Google Sheets للعضوية والحملات والتبرعات والانتخابات والأصوات مع إبقاء تسجيل الدخول والجلسات في Django وقاعدة بياناته:

- اضبط `SHEETS_STORAGE_ENABLED=1`، و`GOOGLE_SHEETS_SPREADSHEET_ID`، و`GOOGLE_SERVICE_ACCOUNT_JSON` في أسرار Render فقط.
- شارك جدول البيانات مع بريد حساب الخدمة بصلاحية Editor، وأنشئ تبويبات `members`, `campaigns`, `donations`, `elections`, `votes`. الصف الأول في كل تبويب هو عناوين الأعمدة؛ العناوين المرجعية موجودة في `backend/sheets_storage/repository.py`.
- عند `SHEETS_STORAGE_ENABLED=0` (الافتراضي) تستخدم الواجهات ORM كما كانت. لا يكتب التطبيق JSON الاعتماد أو أي سر إلى الملفات.
- طبقة Sheets لا تستبدل Django auth ولا إدارة Django؛ كما أن عمليات الإدارة من `/admin/` تبقى ORM، لذلك يلزم إدخال الحملات/الانتخابات إلى التبويبات عند تشغيل Sheets أو تنفيذ مزامنة إدارية لاحقة.

## 5. إعداد البيانات والإدارة

بعد أول نشر، أنشئ مستخدم مدير باستخدام Render Shell:

```bash
python manage.py createsuperuser
```

من `/admin/` أنشئ الانتخابات والمرشحين والحملات، ثم راجع طلبات ربط العضوية. يجب أن يطابق رقم العضوية والاسم واسم العائلة سجل الجمعية قبل اعتماد الحساب. وحدها التبرعات التي يؤكد أمين الصندوق استلامها تحتسب في مجاميع الحملات.

لا توجد حالياً بوابة دفع إلكتروني. تسجّل الواجهة طلبات مساهمة نقدية أو حوالة بنكية فقط، وتظل معلقة حتى مراجعتها.
