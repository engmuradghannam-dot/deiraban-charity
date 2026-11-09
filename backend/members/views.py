import os
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.shortcuts import get_object_or_404
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from sheets_storage import SheetsRepository, sheets_enabled
from .models import Member
from .serializers import MemberRegisterSerializer, MemberSerializer


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = os.getenv("GOOGLE_CALLBACK_URL", "http://localhost:5173")
    client_class = OAuth2Client


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
