from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from unittest.mock import patch
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

    def test_member_can_update_personal_data_and_upload_id(self):
        response = self.client.patch(
            "/api/members/me/personal/",
            {
                "national_id": "9900112233",
                "phone": "0790000000",
                "phone_secondary": "0780000000",
                "email": "member@example.com",
                "id_scan": SimpleUploadedFile("id.png", b"fake-image", content_type="image/png"),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["has_id_scan"])
        profile = Member.objects.get(user=self.user)
        self.assertEqual(profile.national_id, "9900112233")
        self.assertEqual(profile.phone_secondary, "0780000000")
        self.assertEqual(self.user.email, "member@example.com")

    @patch("members.views.requests.get")
    def test_member_can_link_verified_google_email(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "aud": "708875573840-vc4ug1oe97nm7bm590dat6h2f36b8f73.apps.googleusercontent.com",
            "email": "google-member@example.com",
            "email_verified": "true",
        }
        response = self.client.post("/api/auth/google/link/", {"id_token": "test-token"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "google-member@example.com")
