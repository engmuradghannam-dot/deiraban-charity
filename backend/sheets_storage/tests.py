import unittest
from decimal import Decimal
from .repository import InMemorySheetsClient, SheetsRepository


class SheetsRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.client = InMemorySheetsClient({
            "campaigns": [{"id": "c1", "title": "دعم الأسر", "description": "", "goal_amount": "100", "is_active": "TRUE"}],
            "donations": [{"id": "d1", "campaign_id": "c1", "amount": "25.00", "status": "completed", "user_id": "7"}],
            "elections": [{"id": "e1", "title": "المجلس", "description": "", "max_choices": "1", "starts_at": "2020-01-01T00:00:00+00:00", "ends_at": "2030-01-01T00:00:00+00:00", "is_active": "TRUE", "results_public": "TRUE", "candidates_json": '[{"id":"11","name":"مرشح"}]'}],
            "votes": [],
        })
        self.repo = SheetsRepository(self.client)

    def test_campaign_collected_comes_from_completed_donations(self):
        campaign = self.repo.campaigns()[0]
        self.assertEqual(campaign["collected"], Decimal("25.00"))
        self.assertEqual(campaign["percent"], 25.0)

    def test_donation_is_appended_as_pending(self):
        row = self.repo.create_donation({"campaign_id": "c1", "amount": Decimal("5.50"), "user_id": "9"})
        self.assertEqual(row["status"], "pending")
        self.assertEqual(len(self.client.read_rows("donations")), 2)

    def test_vote_is_single_use_and_results_are_aggregated(self):
        self.repo.record_vote("e1", "7", [11])
        with self.assertRaises(ValueError):
            self.repo.record_vote("e1", "7", [11])
        rows, ballots, selections = self.repo.results("e1")
        self.assertEqual((ballots, selections), (1, 1))
        self.assertEqual(rows[0]["votes"], 1)

    def test_personal_data_is_upserted_by_membership_number(self):
        self.repo.save_member_personal_data({
            "membership_number": "7",
            "full_name": "أحمد علاء الدين",
            "family_name": "الدعامسه",
            "national_id": "11111",
            "phone": "0795018444",
            "email": "member@example.com",
        })
        self.repo.save_member_personal_data({
            "membership_number": "7",
            "full_name": "أحمد علاء الدين",
            "family_name": "الدعامسه",
            "national_id": "22222",
        })
        rows = self.client.read_rows("بيانات الأعضاء")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["national_id"], "22222")


if __name__ == "__main__":
    unittest.main()
