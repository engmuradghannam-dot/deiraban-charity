import logging
import mimetypes
import os
import requests
from django.http import FileResponse
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import generics, permissions, serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from sheets_storage import SheetsRepository, sheets_enabled
from .models import Member
from .serializers import MemberPersonalDataSerializer, MemberRegisterSerializer, MemberSerializer, PublicMemberApplicationSerializer, normalize_name

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
        member_id = str(request.data.get("member_id", "")).strip()
        if not full_name and not member_id:
            return Response({"detail": "اختر اسم العضو من قائمة الاقتراحات."}, status=status.HTTP_400_BAD_REQUEST)

        repository = None
        if sheets_enabled() or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip():
            try:
                repository = SheetsRepository()
            except RuntimeError:
                repository = None
        row = repository.member_for_id(member_id) if repository and member_id else None
        if not row and repository and full_name and membership_number:
            row = repository.member_for_credentials(full_name, membership_number)
        if row and not full_name:
            full_name = " ".join(filter(None, [row.get("full_name"), row.get("family_name")])).strip()
        if row and not membership_number:
            membership_number = str(row.get("membership_number", "")).strip()
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
                return Response({"detail": "لم نجد العضو المختار. أعد البحث واختر اسمًا من القائمة."}, status=status.HTTP_401_UNAUTHORIZED)

        if not membership_number:
            return Response({"detail": "هذا العضو لا يملك رقم عضوية معتمدًا بعد. تواصل مع الإدارة."}, status=status.HTTP_403_FORBIDDEN)

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
        member_payload = None
        if row:
            member_payload = {**row}
            member_payload.setdefault("status", "pending")
            member_payload.setdefault("is_eligible_to_vote", member_payload.get("status") in {"approved", "عضو فاعل", "active"})
            profile = Member.objects.filter(user=user).first()
            if profile:
                member_payload.update({
                    "national_id": profile.national_id,
                    "phone": profile.phone or member_payload.get("phone", ""),
                    "phone_secondary": profile.phone_secondary,
                    "email": user.email,
                    "has_profile_photo": bool(profile.profile_photo),
                    "has_id_scan": bool(profile.id_scan),
                    "has_family_book_scan": bool(profile.family_book_scan),
                })
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {"id": user.pk, "username": user.username, "full_name": full_name},
            "member": member_payload,
        })


class MemberSearch(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        query = str(request.query_params.get("q", "")).strip()
        if len(normalize_name(query)) < 2:
            return Response({"results": []})
        repository = None
        if sheets_enabled() or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip():
            try:
                repository = SheetsRepository()
            except RuntimeError:
                repository = None
        results = repository.search_members(query) if repository else []
        response = Response({"results": results})
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response


class MyMemberView(generics.RetrieveAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        if sheets_enabled():
            try:
                repository = SheetsRepository()
            except RuntimeError:
                repository = None
            if repository is None:
                return super().retrieve(request, *args, **kwargs)
            row = repository.member_for_user(request.user.pk)
            if not row:
                membership_number = str(request.user.username).removeprefix("member-")
                row = repository.member_for_credentials(request.user.first_name, membership_number)
            if not row:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            row.setdefault("status", "pending")
            row.setdefault("is_eligible_to_vote", row.get("status") in {"approved", "عضو فاعل", "active"})
            profile = Member.objects.filter(user=request.user).first()
            if profile:
                row.update({
                    "national_id": profile.national_id,
                    "phone": profile.phone or row.get("phone", ""),
                    "phone_secondary": profile.phone_secondary,
                    "email": request.user.email,
                    "has_profile_photo": bool(profile.profile_photo) if profile else False,
                    "has_id_scan": bool(profile.id_scan),
                    "has_family_book_scan": bool(profile.family_book_scan),
                })
            response = Response(row)
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return response
        return super().retrieve(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(Member.objects.select_related("registry_member"), user=self.request.user)


class MyMemberPersonalDataView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = MemberPersonalDataSerializer

    def get_or_create_profile(self):
        profile, _ = Member.objects.get_or_create(
            user=self.request.user,
            defaults={
                "full_name": self.request.user.first_name or self.request.user.username,
                "family_name": "غير محدد",
                "membership_number": str(self.request.user.username).removeprefix("member-") or None,
                "status": Member.Status.PENDING,
            },
        )
        return profile

    def get(self, request, *args, **kwargs):
        return Response(self.get_serializer(self.get_or_create_profile()).data)

    def patch(self, request, *args, **kwargs):
        profile = self.get_or_create_profile()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MyMemberProfilePhotoView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile = Member.objects.filter(user=request.user).first()
        if not profile or not profile.profile_photo:
            return Response({"detail": "لا توجد صورة شخصية مرفوعة."}, status=status.HTTP_404_NOT_FOUND)
        content_type = mimetypes.guess_type(profile.profile_photo.name)[0] or "image/jpeg"
        response = FileResponse(profile.profile_photo.open("rb"), content_type=content_type)
        response["Cache-Control"] = "private, no-store"
        return response


class RegisterMemberView(generics.CreateAPIView):
    serializer_class = MemberRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if not sheets_enabled():
                return Response({"detail": "التسجيل العام متاح عند تفعيل تخزين Google Sheets."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            serializer = PublicMemberApplicationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            repository = SheetsRepository()
            data = serializer.validated_data
            if repository.member_for_name(data["full_name"], data["family_name"]):
                return Response({"detail": "هذا الاسم موجود في سجل الجمعية. استخدم استرجاع رقم العضوية أو تواصل مع الإدارة."}, status=status.HTTP_409_CONFLICT)
            if repository.member_application_for_name(data["full_name"], data["family_name"]):
                return Response({"detail": "يوجد طلب تسجيل بهذا الاسم قيد المراجعة. لا يمكن إرسال طلب مكرر."}, status=status.HTTP_409_CONFLICT)
            application = repository.create_member_application(data)
            return Response(
                {**application, "message": "تم استلام طلب التسجيل، وستراجعه الإدارة وتحدد رقم العضوية لاحقًا."},
                status=status.HTTP_201_CREATED,
            )
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
