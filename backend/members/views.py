import os

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.shortcuts import get_object_or_404
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import generics, permissions, serializers

from .models import Member
from .serializers import MemberRegisterSerializer, MemberSerializer


class GoogleLogin(SocialLoginView):
    """تسجيل الدخول عبر Google باستعمال authorization code."""

    adapter_class = GoogleOAuth2Adapter
    callback_url = os.getenv("GOOGLE_CALLBACK_URL", "http://localhost:5173")
    client_class = OAuth2Client


class MyMemberView(generics.RetrieveAPIView):
    """بيانات العضو الحالي واشتراكاته السنوية."""

    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_object_or_404(Member.objects.select_related("registry_member"), user=self.request.user)


class RegisterMemberView(generics.CreateAPIView):
    """إنشاء طلب ربط حساب بسجل رسمي؛ يظل معلقاً حتى موافقة الإدارة."""

    serializer_class = MemberRegisterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if Member.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError({"detail": "لديك طلب عضوية مسجل بالفعل."})
        serializer.save(user=self.request.user, status=Member.Status.PENDING)
