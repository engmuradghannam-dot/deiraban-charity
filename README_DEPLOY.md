# نشر المشروع على Render — دليل سريع

هذا الباتش يجهّز مشروعك للنشر. خطوات التطبيق:

## 1) انسخ الملفات التالية فوق نفس المسارات في مشروعك المحلي (C:\deraban_project)

- `backend/requirements.txt` → استبدل الموجود
- `backend/deraban/settings.py` → استبدل الموجود
- `frontend/src/api.js` → استبدل الموجود
- `render.yaml` → ضعه في **جذر المشروع** (C:\deraban_project\render.yaml، بجانب README.md الأصلي)

## 2) ارفعها إلى GitHub

```
cd C:\deraban_project
git add -A
git commit -m "تجهيز النشر على Render: gunicorn, whitenoise, إعدادات إنتاجية"
git push
```

## 3) على موقع Render (هذا الجزء الوحيد اللي لازم تسويه إنت بنفسك — يحتاج حسابك)

1. افتح https://render.com وسجّل دخول بزر **"Sign in with GitHub"**
2. من اللوحة: **New +** → **Blueprint**
3. اختر مستودع `deiraban-charity` — Render بيقرأ `render.yaml` تلقائياً ويجهز الخدمتين (backend + frontend) بضغطة **Apply** وحدة
4. انتظر لين يخلص أول نشر (5-10 دقائق) — بيطلع لك رابطين:
   - `https://deraban-backend-xxxx.onrender.com`
   - `https://deraban-frontend-xxxx.onrender.com`

## 4) الخطوة الأخيرة (إلزامية) — ربط الرابطين ببعض

لازم تدخل كل خدمة من لوحة Render وتضيف يدوياً قيمة متغير بيئي واحد (لأن كل خدمة تحتاج تعرف رابط الثانية، وهذا ما يُعرف إلا بعد أول نشر):

- داخل خدمة **deraban-backend** → Environment → عدّل `CORS_ALLOWED_ORIGINS` لتكون رابط الفرونت كامل، مثال:
  `https://deraban-frontend-xxxx.onrender.com`
- داخل خدمة **deraban-frontend** → Environment → عدّل `VITE_API_BASE` لتكون رابط الباكند كامل، مثال:
  `https://deraban-backend-xxxx.onrender.com`

بعد كل تعديل اضغط **Save, rebuild, and deploy** (يطلع تلقائياً بعد التعديل).

## ملاحظات

- الخطة المجانية على Render "تنام" الخدمة بعد 15 دقيقة من عدم الاستخدام، وأول طلب بعدها ياخذ 30-50 ثانية حتى تصحى. هذا طبيعي بالخطة المجانية.
- بيانات الأعضاء (887 عضواً) تُستورد تلقائياً أثناء البناء عبر `import_members` — موجودة فعلاً بالمستودع العام، فإذا تبي تقفل الوصول عنها راجع ملاحظة الخصوصية في المحادثة السابقة (الأفضل تخلي المستودع Private).
- لإنشاء حساب مدير (Django Admin) على السيرفر المنشور: من لوحة Render → خدمة deraban-backend → تبويب **Shell** → نفّذ:
  ```
  python manage.py createsuperuser
  ```
