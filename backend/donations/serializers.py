from decimal import Decimal

from rest_framework import serializers

from .models import Donation, DonationCampaign


class CampaignSerializer(serializers.ModelSerializer):
    collected = serializers.ReadOnlyField()
    percent = serializers.SerializerMethodField()

    class Meta:
        model = DonationCampaign
        fields = ["id", "title", "description", "goal_amount", "collected", "percent", "is_active", "created_at"]

    def get_percent(self, obj):
        if not obj.goal_amount:
            return None
        return round(float(obj.collected) / float(obj.goal_amount) * 100, 1)


class DonationCreateSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    donor_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    donor_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)

    class Meta:
        model = Donation
        fields = ["campaign", "amount", "method", "donor_name", "donor_phone", "notes"]

    def validate_campaign(self, campaign):
        if campaign and not campaign.is_active:
            raise serializers.ValidationError("هذه الحملة غير مفعّلة.")
        return campaign

    def validate(self, attrs):
        request = self.context["request"]
        if not request.user.is_authenticated and not attrs.get("donor_name", "").strip():
            raise serializers.ValidationError({"donor_name": "الاسم مطلوب عند التبرع كزائر."})
        return attrs


class MyDonationSerializer(serializers.ModelSerializer):
    campaign_title = serializers.CharField(source="campaign.title", read_only=True, default="تبرع عام")
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    method_label = serializers.CharField(source="get_method_display", read_only=True)

    class Meta:
        model = Donation
        fields = [
            "id", "campaign_title", "amount", "currency", "method", "method_label",
            "status", "status_label", "created_at",
        ]
