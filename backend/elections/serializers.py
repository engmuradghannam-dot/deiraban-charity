from rest_framework import serializers
from .models import Election, Candidate, Ballot


class CandidateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='member.full_name', read_only=True)
    family_name = serializers.CharField(source='member.family_name', read_only=True)
    photo = serializers.ImageField(read_only=True)

    class Meta:
        model = Candidate
        fields = ['id', 'name', 'family_name', 'bio', 'photo']


class ElectionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)
    is_open = serializers.ReadOnlyField()
    status_label = serializers.ReadOnlyField()
    has_voted = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'max_choices', 'starts_at',
                  'ends_at', 'is_active', 'is_open', 'status_label',
                  'results_public', 'candidates', 'has_voted']

    def get_has_voted(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        member = getattr(request.user, 'member_profile', None)
        return bool(member and Ballot.objects.filter(
            election=obj, voter=member
        ).exists())
