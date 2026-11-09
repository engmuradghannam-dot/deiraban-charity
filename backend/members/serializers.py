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


class MemberRegisterSerializer(serializers.ModelSerializer):
    membership_number = serializers.CharField(write_only=True, max_length=20)
    full_name = serializers.CharField(max_length=255, trim_whitespace=True)
    family_name = serializers.CharField(max_length=100, trim_whitespace=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    class Meta:
        model = Member
        fields = ["membership_number", "full_name", "family_name", "phone"]

    def validate(self, attrs):
        number = attrs["membership_number"].strip()
        registry = (
            RegistryMember.objects.select_related("family")
            .filter(membership_number=number)
            .first()
        )
        if not registry:
            raise serializers.ValidationError({
                "membership_number": "تعذر مطابقة رقم العضوية مع سجل الجمعية. راجع الإدارة إذا كنت تعتقد أن الرقم صحيح."
            })
        if (
            normalize_name(attrs["full_name"]) != normalize_name(registry.full_name)
            or normalize_name(attrs["family_name"]) != normalize_name(registry.family.name)
        ):
            raise serializers.ValidationError({
                "membership_number": "لم يتطابق الاسم أو اسم العائلة مع سجل العضوية."
            })
        if Member.objects.filter(registry_member=registry).exists():
            raise serializers.ValidationError({
                "membership_number": "تم ربط هذا الرقم بحساب عضو مسبقاً. تواصل مع الإدارة للمساعدة."
            })
        attrs["membership_number"] = registry.membership_number
        attrs["registry_member"] = registry
        attrs["membership_type"] = (
            Member.Type.ACTIVE
            if registry.status == RegistryMember.STATUS_ACTIVE
            else Member.Type.INACTIVE
        )
        return attrs
