from rest_framework import serializers
from .models import DonationCampaign, Donation


class CampaignSerializer(serializers.ModelSerializer):
    collected = serializers.ReadOnlyField()
    percent = serializers.SerializerMethodField()

    class Meta:
        model = DonationCampaign
        fields = ['id', 'title', 'description', 'goal_amount', 'collected',
                  'percent', 'is_active', 'created_at']

    def get_percent(self, obj):
        if not obj.goal_amount:
            return None
        return round(float(obj.collected) / float(obj.goal_amount) * 100, 1)


class DonationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = ['campaign', 'amount', 'currency', 'method', 'donor_name',
                  'donor_phone', 'notes']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('المبلغ يجب أن يكون أكبر من صفر.')
        return value

    def validate(self, attrs):
        request = self.context['request']
        if not request.user.is_authenticated and not attrs.get('donor_name'):
            raise serializers.ValidationError(
                {'donor_name': 'الاسم مطلوب عند التبرع كزائر.'}
            )
        if attrs.get('campaign') and not attrs['campaign'].is_active:
            raise serializers.ValidationError(
                {'campaign': 'هذه الحملة غير مفعّلة.'}
            )
        return attrs


class MyDonationSerializer(serializers.ModelSerializer):
    campaign_title = serializers.CharField(
        source='campaign.title', read_only=True, default='تبرع عام'
    )

    class Meta:
        model = Donation
        fields = ['id', 'campaign_title', 'amount', 'currency', 'method',
                  'status', 'created_at']
