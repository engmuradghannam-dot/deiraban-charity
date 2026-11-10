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
from .serializers import MemberRegisterSerializer, MemberSerializer

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


class MyMemberView(generics.RetrieveAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        if sheets_enabled():
            row = SheetsRepository().member_for_user(request.user.pk)
            if not row:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
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
        if SheetsRepository().member_for_user(request.user.pk):
            raise serializers.ValidationError({"detail": "لديك طلب عضوية مسجل بالفعل."})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registry = serializer.validated_data.get("registry_member")
        row = {"user_id": str(request.user.pk), "membership_number": serializer.validated_data["membership_number"], "full_name": serializer.validated_data["full_name"], "family_name": serializer.validated_data["family_name"], "phone": serializer.validated_data.get("phone", ""), "membership_type": serializer.validated_data["membership_type"], "status": Member.Status.PENDING}
        return Response(SheetsRepository().create_member(row), status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        if Member.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError({"detail": "لديك طلب عضوية مسجل بالفعل."})
        serializer.save(user=self.request.user, status=Member.Status.PENDING)
