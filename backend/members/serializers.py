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
