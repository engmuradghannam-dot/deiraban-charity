import re
import unicodedata

from rest_framework import serializers

from membership.models import Member as RegistryMember
from .models import Member, MembershipFee


def normalize_name(value):
    value = unicodedata.normalize("NFKC", value or "").replace("ـ", "")
    value = re.sub(r"[\u064B-\u065F\u0670]", "", value)
    return " ".join(value.casefold().split())


class MembershipFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipFee
        fields = ["year", "amount", "paid", "paid_at"]


class MemberSerializer(serializers.ModelSerializer):
    fees = MembershipFeeSerializer(many=True, read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    is_eligible_to_vote = serializers.ReadOnlyField()

    class Meta:
        model = Member
        fields = [
            "id",
            "membership_number",
            "full_name",
            "family_name",
            "phone",
            "membership_type",
            "status",
            "is_eligible_to_vote",
            "email",
            "fees",
            "created_at",
        ]
        read_only_fields = ["status", "membership_number", "membership_type"]


class MemberPersonalDataSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True, write_only=True)
    has_id_scan = serializers.SerializerMethodField()
    has_family_book_scan = serializers.SerializerMethodField()
    has_profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            "national_id", "phone", "phone_secondary", "email",
            "profile_photo", "id_scan", "family_book_scan",
            "has_profile_photo", "has_id_scan", "has_family_book_scan",
        ]
        extra_kwargs = {
            "profile_photo": {"write_only": True, "required": False},
            "id_scan": {"write_only": True, "required": False},
            "family_book_scan": {"write_only": True, "required": False},
        }

    def get_has_id_scan(self, obj):
        return bool(obj.id_scan)

    def get_has_profile_photo(self, obj):
        return bool(obj.profile_photo)

    def get_has_family_book_scan(self, obj):
        return bool(obj.family_book_scan)

    def validate_profile_photo(self, upload):
        if upload and upload.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("حجم الصورة يجب ألا يتجاوز 5 ميغابايت.")
        if upload and upload.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise serializers.ValidationError("يسمح برفع صورة JPG أو PNG أو WEBP فقط.")
        return upload

    @staticmethod
    def _validate_document(upload):
        if upload and upload.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("حجم الملف يجب ألا يتجاوز 10 ميغابايت.")
        if upload and upload.content_type not in {"application/pdf", "image/jpeg", "image/png", "image/webp"}:
            raise serializers.ValidationError("يسمح برفع PDF أو JPG أو PNG أو WEBP فقط.")
        return upload

    def validate_id_scan(self, upload):
        return self._validate_document(upload)

    def validate_family_book_scan(self, upload):
        return self._validate_document(upload)

    def update(self, instance, validated_data):
        email = validated_data.pop("email", None)
        if email is not None:
            instance.user.email = email.strip().lower()
            instance.user.save(update_fields=["email"])
        return super().update(instance, validated_data)


class MemberRegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=255, trim_whitespace=True)
    family_name = serializers.CharField(max_length=100, trim_whitespace=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    class Meta:
        model = Member
        fields = ["full_name", "family_name", "phone"]

    def validate(self, attrs):
        registry = next(
            (
                item for item in RegistryMember.objects.select_related("family").all()
                if normalize_name(item.full_name) == normalize_name(attrs["full_name"])
                and normalize_name(item.family.name) == normalize_name(attrs["family_name"])
            ),
            None,
        )
        if registry and Member.objects.filter(registry_member=registry).exists():
            raise serializers.ValidationError({"full_name": "هذا العضو مسجل بالفعل. يمكنك متابعة الدخول من حساب Google."})
        attrs["registry_member"] = registry
        attrs["membership_number"] = registry.membership_number if registry else None
        attrs["membership_type"] = (
            Member.Type.ACTIVE if registry and registry.status == RegistryMember.STATUS_ACTIVE else Member.Type.INACTIVE
        )
        return attrs


class PublicMemberApplicationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255, trim_whitespace=True)
    family_name = serializers.CharField(max_length=100, trim_whitespace=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_full_name(self, value):
        if len(normalize_name(value).split()) < 3:
            raise serializers.ValidationError("يجب كتابة الاسم الثلاثي على الأقل.")
        return value
