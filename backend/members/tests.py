from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from membership.models import Family, Member as RegistryMember
from .models import Member

User = get_user_model()


class MemberRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="member-user", password="test-pass")
        self.family = Family.objects.create(name="آل الهاشمي")
        self.registry = RegistryMember.objects.create(
            membership_number="A-220",
            full_name="محمد أحمد الهاشمي",
            family=self.family,
            status=RegistryMember.STATUS_ACTIVE,
        )
        self.client.force_authenticate(self.user)

    def test_matching_registry_record_creates_pending_profile(self):
        response = self.client.post(
            "/api/members/register/",
            {
                "full_name": "محمد  أحمد الهاشمي",
                "family_name": "آل الهاشمي",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        profile = Member.objects.get(user=self.user)
        self.assertEqual(profile.registry_member, self.registry)
        self.assertEqual(profile.status, Member.Status.PENDING)
        self.assertFalse(profile.is_eligible_to_vote)

    def test_new_name_creates_pending_profile_without_membership_number(self):
        response = self.client.post(
            "/api/members/register/",
            {
                "full_name": "اسم مختلف",
                "family_name": "آل الهاشمي",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        profile = Member.objects.get(user=self.user)
        self.assertIsNone(profile.registry_member)
        self.assertIsNone(profile.membership_number)
        self.assertEqual(profile.status, Member.Status.PENDING)

    def test_approval_enables_voting_only_when_registry_is_active(self):
        profile = Member.objects.create(
            user=self.user,
            registry_member=self.registry,
            membership_number=self.registry.membership_number,
            full_name=self.registry.full_name,
            family_name=self.family.name,
            membership_type=Member.Type.ACTIVE,
            status=Member.Status.PENDING,
        )
        self.assertFalse(profile.is_eligible_to_vote)
        profile.status = Member.Status.APPROVED
        profile.save(update_fields=["status"])
        self.assertTrue(profile.is_eligible_to_vote)

    def test_member_password_login_returns_jwt_for_matching_registry(self):
        response = self.client.post(
            "/api/auth/member-login/",
            {"full_name": "محمد أحمد الهاشمي", "membership_number": "A-220"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["full_name"], "محمد أحمد الهاشمي")

    def test_member_recovery_returns_membership_number_for_matching_name(self):
        response = self.client.post(
            "/api/auth/member-recovery/",
            {"full_name": "محمد أحمد الهاشمي", "family_name": "آل الهاشمي"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["membership_number"], "A-220")
