from rest_framework import serializers

from .models import Candidate, Election, VoterParticipation


class CandidateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="member.full_name", read_only=True)
    family_name = serializers.CharField(source="member.family_name", read_only=True)
    photo = serializers.ImageField(read_only=True)

    class Meta:
        model = Candidate
        fields = ["id", "name", "family_name", "bio", "photo"]


class ElectionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)
    is_open = serializers.ReadOnlyField()
    status_label = serializers.ReadOnlyField()
    has_voted = serializers.SerializerMethodField()
    eligible_to_vote = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = [
            "id", "title", "description", "max_choices", "starts_at", "ends_at",
            "is_active", "is_open", "status_label", "results_public", "candidates",
            "has_voted", "eligible_to_vote",
        ]

    def _member(self):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        return getattr(request.user, "member_profile", None)

    def get_has_voted(self, obj):
        member = self._member()
        return bool(member and VoterParticipation.objects.filter(election=obj, voter=member).exists())

    def get_eligible_to_vote(self, obj):
        member = self._member()
        return bool(member and member.is_eligible_to_vote)


class VoteSubmissionSerializer(serializers.Serializer):
    candidate_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False, max_length=100
    )

    def validate_candidate_ids(self, candidate_ids):
        election = self.context["election"]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise serializers.ValidationError("لا تكرر اختيار المرشح نفسه.")
        if len(candidate_ids) > election.max_choices:
            raise serializers.ValidationError(
                f"يمكنك اختيار {election.max_choices} مرشحين كحد أقصى."
            )
        return candidate_ids
