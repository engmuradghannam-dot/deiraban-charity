import os

import requests
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import AidRequest
from .serializers import AidRequestSerializer

# نفس عميل جوجل الافتراضي المستخدم في تطبيق members (GoogleLogin) حتى يبقى
# متوافقاً مع نفس GOOGLE_CLIENT_ID المضبوط في إعدادات المشروع.
_DEFAULT_GOOGLE_CLIENT_ID = "708875573840-vc4ug1oe97nm7bm590dat6h2f36b8f73.apps.googleusercontent.com"


def _verify_google_id_token(token):
    """
    يتحقق من id_token القادم من Google Sign-In عبر endpoint التحقق الرسمي من
    جوجل مباشرة (نفس الأسلوب المستخدم في members.views.GoogleLogin).
    يرجع (True, payload) أو (False, رسالة الخطأ).
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip() or _DEFAULT_GOOGLE_CLIENT_ID
    try:
        resp = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": token},
            timeout=10,
        )
    except requests.RequestException:
        return False, "تعذر التحقق من حساب جوجل، حاول مرة أخرى"

    if resp.status_code != 200:
        return False, "رمز الدخول غير صالح أو منتهي"

    payload = resp.json()
    if payload.get("aud") != client_id:
        return False, "رمز الدخول غير مخصص لهذا الموقع"

    if payload.get("email_verified") not in ("true", True):
        return False, "البريد الإلكتروني غير موثّق من جوجل"

    return True, payload


class AidRequestAdminViewSet(viewsets.ModelViewSet):
    """مراجعة طلبات المساعدة — للأدمن فقط (قبول/رفض/ملاحظات)."""

    queryset = AidRequest.objects.all()
    serializer_class = AidRequestSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["status"]
    search_fields = ["full_name", "family_name", "phone", "national_id", "email"]
    ordering_fields = ["created_at", "full_name"]


@api_view(["POST"])
@permission_classes([AllowAny])
def register_aid_request(request):
    """
    تسجيل طلب مساعدة جديد — مفتوح للعموم عبر تسجيل الدخول بحساب Google.
    يستقبل: id_token (من Google Sign-In) + بيانات الطلب.
    لو سبق لنفس حساب جوجل أنه قدّم طلباً، يتم تحديث بياناته بدل تكرار الطلب.
    """
    token = request.data.get("id_token")
    if not token:
        return Response({"detail": "رمز دخول جوجل مفقود"}, status=http_status.HTTP_400_BAD_REQUEST)

    ok, payload = _verify_google_id_token(token)
    if not ok:
        return Response({"detail": payload}, status=http_status.HTTP_401_UNAUTHORIZED)

    google_sub = payload.get("sub")
    email = payload.get("email", "")
    google_name = payload.get("name", "")

    existing = AidRequest.objects.filter(google_sub=google_sub).first()

    data = {
        "google_sub": google_sub,
        "email": email,
        "full_name": request.data.get("full_name") or google_name,
        "family_name": request.data.get("family_name", ""),
        "phone": request.data.get("phone", ""),
        "national_id": request.data.get("national_id", ""),
        "address": request.data.get("address", ""),
        "need_description": request.data.get("need_description", ""),
    }

    if existing:
        serializer = AidRequestSerializer(existing, data=data, partial=True)
    else:
        serializer = AidRequestSerializer(data=data)

    serializer.is_valid(raise_exception=True)
    # أي تقديم أو إعادة تقديم يرجع الطلب لحالة "قيد المراجعة" من جديد.
    instance = serializer.save(status=AidRequest.Status.PENDING)

    return Response(
        AidRequestSerializer(instance).data,
        status=http_status.HTTP_200_OK if existing else http_status.HTTP_201_CREATED,
    )
