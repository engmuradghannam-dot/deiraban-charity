from rest_framework import serializers
from .models import Member, MembershipFee


class MembershipFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipFee
        fields = ['year', 'amount', 'paid', 'paid_at']


class MemberSerializer(serializers.ModelSerializer):
    fees = MembershipFeeSerializer(many=True, read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Member
        fields = [
            'id', 'membership_number', 'full_name', 'family_name',
            'national_id', 'phone', 'membership_type', 'status',
            'notes', 'email', 'fees', 'created_at',
        ]
        read_only_fields = ['status', 'membership_number']


class MemberRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['full_name', 'family_name', 'national_id', 'phone',
                  'membership_type', 'notes']
