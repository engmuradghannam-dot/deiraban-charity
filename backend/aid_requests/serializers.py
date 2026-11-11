from rest_framework import serializers

from .models import AidRequest


class AidRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AidRequest
        fields = [
            "id",
            "google_sub",
            "email",
            "full_name",
            "family_name",
            "phone",
            "national_id",
            "address",
            "need_description",
            "status",
            "reviewer_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"google_sub": {"write_only": True}}
