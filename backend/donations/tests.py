from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Donation, DonationCampaign

User = get_user_model()


class DonationFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.campaign = DonationCampaign.objects.create(
            title="دعم الأسر",
            goal_amount=Decimal("1000.00"),
            is_active=True,
        )

    def test_cash_request_stays_pending_until_admin_confirms_receipt(self):
        response = self.client.post(
            "/api/donations/",
            {
                "campaign": self.campaign.id,
                "amount": "25.00",
                "method": "cash",
                "donor_name": "متبرع كريم",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        donation = Donation.objects.get()
        self.assertEqual(donation.status, Donation.Status.PENDING)
        self.assertEqual(self.campaign.collected, Decimal("0"))

        donation.status = Donation.Status.COMPLETED
        donation.save(update_fields=["status"])
        self.assertEqual(self.campaign.collected, Decimal("25.00"))

    def test_online_payment_is_not_accepted_without_a_gateway(self):
        response = self.client.post(
            "/api/donations/",
            {"amount": "10.00", "method": "online", "donor_name": "متبرع"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Donation.objects.count(), 0)

    def test_logged_in_donor_can_view_their_own_requests(self):
        user = User.objects.create_user(username="donor", email="donor@example.test", password="test-pass")
        self.client.force_authenticate(user)
        created = self.client.post(
            "/api/donations/",
            {"campaign": self.campaign.id, "amount": "8.50", "method": "bank"},
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(Donation.objects.get().user, user)

        response = self.client.get("/api/donations/mine/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], Donation.Status.PENDING)

    def test_guest_name_and_positive_amount_are_required(self):
        missing_name = self.client.post(
            "/api/donations/", {"amount": "5", "method": "bank"}, format="json"
        )
        self.assertEqual(missing_name.status_code, 400)
        zero_amount = self.client.post(
            "/api/donations/",
            {"amount": "0", "method": "bank", "donor_name": "متبرع"},
            format="json",
        )
        self.assertEqual(zero_amount.status_code, 400)
