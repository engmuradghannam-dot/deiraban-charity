from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from membership.models import Family, Member as RegistryMember
from members.models import Member
from .models import Ballot, Candidate, Election, VoterParticipation

User = get_user_model()


class ElectionVotingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        family = Family.objects.create(name="آل مثال")
        self.voter_user = User.objects.create_user(username="voter", password="test-pass")
        self.voter = self.make_profile("M100", "ناخب مثال", family, self.voter_user)
        self.candidate_one = self.make_profile("M101", "مرشح أول", family)
        self.candidate_two = self.make_profile("M102", "مرشح ثان", family)
        now = timezone.now()
        self.election = Election.objects.create(
            title="انتخابات المجلس",
            starts_at=now - timedelta(hours=1),
            ends_at=now + timedelta(hours=1),
            max_choices=2,
        )
        self.candidate_record_one = Candidate.objects.create(election=self.election, member=self.candidate_one)
        self.candidate_record_two = Candidate.objects.create(election=self.election, member=self.candidate_two)
        self.client.force_authenticate(self.voter_user)

    def make_profile(self, number, name, family, user=None, registry_status=RegistryMember.STATUS_ACTIVE):
        registry = RegistryMember.objects.create(
            membership_number=number,
            full_name=name,
            family=family,
            status=registry_status,
        )
        return Member.objects.create(
            user=user,
            registry_member=registry,
            membership_number=number,
            full_name=name,
            family_name=family.name,
            membership_type=(Member.Type.ACTIVE if registry_status == RegistryMember.STATUS_ACTIVE else Member.Type.INACTIVE),
            status=Member.Status.APPROVED,
        )

    def test_approved_active_member_can_vote_once_without_ballot_identity_link(self):
        response = self.client.post(
            f"/api/elections/{self.election.id}/vote/",
            {"candidate_ids": [self.candidate_record_one.id]},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(VoterParticipation.objects.filter(election=self.election, voter=self.voter).count(), 1)
        self.assertEqual(Ballot.objects.filter(election=self.election).count(), 1)
        self.assertFalse(hasattr(Ballot.objects.get(election=self.election), "voter"))

        duplicate = self.client.post(
            f"/api/elections/{self.election.id}/vote/",
            {"candidate_ids": [self.candidate_record_two.id]},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(Ballot.objects.filter(election=self.election).count(), 1)

    def test_unregistered_candidate_is_rejected(self):
        response = self.client.post(
            f"/api/elections/{self.election.id}/vote/",
            {"candidate_ids": [999999]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(VoterParticipation.objects.filter(election=self.election, voter=self.voter).exists())

    def test_inactive_registry_member_cannot_vote(self):
        inactive_user = User.objects.create_user(username="inactive", password="test-pass")
        inactive = self.make_profile(
            "M103", "عضو غير فاعل", self.voter.registry_member.family,
            inactive_user, RegistryMember.STATUS_INACTIVE,
        )
        self.client.force_authenticate(inactive_user)
        response = self.client.post(
            f"/api/elections/{self.election.id}/vote/",
            {"candidate_ids": [self.candidate_record_one.id]},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(VoterParticipation.objects.filter(election=self.election, voter=inactive).exists())

    def test_results_stay_hidden_when_not_public_during_open_election(self):
        self.election.results_public = False
        self.election.save(update_fields=["results_public"])
        response = self.client.get(f"/api/elections/{self.election.id}/results/")
        self.assertEqual(response.status_code, 403)
