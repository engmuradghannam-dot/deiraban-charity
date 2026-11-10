import logging
import os
import requests
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from sheets_storage import SheetsRepository, sheets_enabled
from .models import Member
from .serializers import MemberRegisterSerializer, MemberSerializer, normalize_name

logger = logging.getLogger(__name__)


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    # Accept Google's standard credential/id_token flow and the legacy access-token flow.
    callback_url = os.getenv("GOOGLE_CALLBACK_URL", "postmessage")
    client_class = OAuth2Client

    def post(self, request, *args, **kwargs):
        try:
            id_token = str(request.data.get("id_token", "")).strip()
            access_token = str(request.data.get("access_token", "")).strip()
            if not id_token and not access_token:
                return Response({"detail": "رمز Google مطلوب."}, status=status.HTTP_400_BAD_REQUEST)
            client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip() or "708875573840-vc4ug1oe97nm7bm590dat6h2f36b8f73.apps.googleusercontent.com"
            token_response = requests.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token} if id_token else {"access_token": access_token},
                timeout=10,
            )
            if token_response.status_code != 200:
                return Response({"detail": "رمز Google غير صالح أو منتهي."}, status=status.HTTP_400_BAD_REQUEST)
            claims = token_response.json()
            if claims.get("aud") != client_id:
                return Response({"detail": "رمز Google لا يخص هذا التطبيق."}, status=status.HTTP_400_BAD_REQUEST)
            email = str(claims.get("email", "")).strip().lower()
            email_verified = claims.get("email_verified", claims.get("verified_email"))
            if not email or email_verified not in {True, "true", "True"}:
                return Response({"detail": "حساب Google لا يحتوي بريدًا موثقًا."}, status=status.HTTP_400_BAD_REQUEST)
            User = get_user_model()
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": email},
            )
            if created:
                user.set_unusable_password()
                user.first_name = str(claims.get("given_name", ""))[:150]
                user.last_name = str(claims.get("family_name", ""))[:150]
                user.save(update_fields=["password", "first_name", "last_name"])
            if not user.is_active:
                return Response({"detail": "هذا الحساب غير نشط."}, status=status.HTTP_403_FORBIDDEN)
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {"id": user.pk, "email": user.email, "first_name": user.first_name, "last_name": user.last_name},
            })
        except Exception:
            logger.exception("Google OAuth verification failed")
            return Response(
                {"detail": "تعذر التحقق من حساب Google. أعد المحاولة أو تحقق من إعداد OAuth."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MemberPasswordLogin(generics.GenericAPIView):
    """تسجيل الدخول باستخدام اسم العضو ورقم العضوية ككلمة مرور."""
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        full_name = str(request.data.get("full_name", "")).strip()
        membership_number = str(request.data.get("membership_number", "")).strip()
        if not full_name or not membership_number:
            return Response({"detail": "اكتب اسم العضو ورقم العضوية."}, status=status.HTTP_400_BAD_REQUEST)

        repository = SheetsRepository() if sheets_enabled() else None
        row = repository.member_for_credentials(full_name, membership_number) if repository else None
        registry = None
        if not row:
            from membership.models import Member as RegistryMember
            registry = next(
                (
                    item for item in RegistryMember.objects.select_related("family").all()
                    if normalize_name(item.full_name) == normalize_name(full_name)
                    and str(item.membership_number).strip().casefold() == membership_number.casefold()
                ),
                None,
            )
            if not registry:
                return Response({"detail": "لم نجد عضوًا بهذا الاسم ورقم العضوية. راجع البيانات أو تواصل مع الإدارة."}, status=status.HTTP_401_UNAUTHORIZED)

        User = get_user_model()
        user = None
        if row and row.get("user_id"):
            try:
                user = User.objects.filter(pk=row["user_id"]).first()
            except (TypeError, ValueError):
                user = None
        username = f"member-{membership_number}"
        if user is None:
            user, _ = User.objects.get_or_create(username=username, defaults={"first_name": full_name[:150]})
        user.set_password(membership_number)
        user.first_name = full_name[:150]
        user.save(update_fields=["password", "first_name"])
        if row and not row.get("user_id"):
            repository.link_member_to_user(row.get("id"), user.pk)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {"id": user.pk, "username": user.username, "full_name": full_name},
        })


class MyMemberView(generics.RetrieveAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        if sheets_enabled():
            repository = SheetsRepository()
            row = repository.member_for_user(request.user.pk)
            if not row:
                membership_number = str(request.user.username).removeprefix("member-")
                row = repository.member_for_credentials(request.user.first_name, membership_number)
            if not row:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            row.setdefault("status", "pending")
            row.setdefault("is_eligible_to_vote", row.get("status") in {"approved", "عضو فاعل", "active"})
            return Response(row)
        return super().retrieve(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(Member.objects.select_related("registry_member"), user=self.request.user)


class RegisterMemberView(generics.CreateAPIView):
    serializer_class = MemberRegisterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not sheets_enabled():
            return super().create(request, *args, **kwargs)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        repository = SheetsRepository()
        if repository.member_for_user(request.user.pk):
            raise serializers.ValidationError({"detail": "لديك تسجيل عضوية مرتبط بهذا الحساب بالفعل."})
        data = serializer.validated_data
        existing = repository.member_for_name(data["full_name"], data["family_name"])
        if existing:
            if existing.get("user_id") and str(existing.get("user_id")) != str(request.user.pk):
                raise serializers.ValidationError({"full_name": "هذا الاسم مسجل بالفعل بحساب Google آخر. تواصل مع الإدارة إذا كان الحساب لك."})
            linked = repository.link_member_to_user(existing.get("id"), request.user.pk, data.get("phone", ""))
            return Response({**(linked or existing), "registration_state": "existing", "message": "تم العثور على تسجيلك في سجل الجمعية. يمكنك المتابعة."}, status=status.HTTP_200_OK)
        row = {"user_id": str(request.user.pk), "membership_number": "", "full_name": data["full_name"], "family_name": data["family_name"], "phone": data.get("phone", ""), "membership_type": Member.Type.INACTIVE, "status": Member.Status.PENDING}
        return Response({**repository.create_member(row), "registration_state": "new", "message": "تم إنشاء طلب عضوية جديد، وسيتم مراجعته من الإدارة."}, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        if Member.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError({"detail": "لديك طلب عضوية مسجل بالفعل."})
        serializer.save(user=self.request.user, status=Member.Status.PENDING)
