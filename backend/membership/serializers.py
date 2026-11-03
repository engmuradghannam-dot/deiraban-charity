from rest_framework import serializers
from .models import Family, Member


class FamilySerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source="members.count", read_only=True)

    class Meta:
        model = Family
        fields = ["id", "name", "member_count"]


class MemberSerializer(serializers.ModelSerializer):
    family_name = serializers.CharField(source="family.name", read_only=True)

    class Meta:
        model = Member
        fields = [
            "id",
            "membership_number",
            "full_name",
            "family",
            "family_name",
            "national_id",
            "status",
            "notes",
            "sub_2019_base",
            "sub_2020",
            "sub_2021",
            "sub_2022",
            "sub_2023",
            "sub_2024",
            "sub_2025",
        ]
