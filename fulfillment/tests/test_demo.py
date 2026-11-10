from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from catalog.demo import seed_demo
from catalog.models import Product, ShippingBox
from fulfillment.domain import FIT, ITEM_TOO_LARGE, TOO_HEAVY
from fulfillment.models import Order
from fulfillment.services import recommend_lines


class DemoRecommendationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_demo()

    def recommend(self, *pairs):
        lines = [(Product.objects.get(sku=sku), quantity) for sku, quantity in pairs]
        return recommend_lines(lines)

    def test_seed_is_idempotent(self):
        seed_demo()
        self.assertEqual(Product.objects.count(), 7)
        self.assertEqual(ShippingBox.objects.count(), 5)

    def test_catalog_scenarios(self):
        cases = [
            ([("PHONE", 1)], "Mailer"),
            ([("BOOK", 1)], "Small"),
            ([("MUG", 1)], "Small"),
            ([("LAPTOP", 1)], "Medium"),
            ([("KETTLEBELL", 1)], "Medium"),
            ([("POSTER", 1)], "Poster tube"),
            ([("DUMBBELL", 1)], "Large"),
            ([("PHONE", 1), ("BOOK", 1)], "Small"),
            ([("BOOK", 6)], "Small"),
            ([("DUMBBELL", 1), ("KETTLEBELL", 1)], "Large"),
            ([("POSTER", 1), ("PHONE", 1)], "Poster tube"),
            ([("DUMBBELL", 1), ("KETTLEBELL", 1), ("PHONE", 1)], None),
        ]
        for pairs, expected in cases:
            with self.subTest(pairs=pairs):
                selection = self.recommend(*pairs)
                if expected is None:
                    self.assertIsNone(selection.recommended)
                    self.assertIn("No shipping box", selection.summary)
                else:
                    self.assertEqual(selection.recommended.box.name, expected)

    def test_kettlebell_reports_size_before_weight_on_the_small_box(self):
        selection = self.recommend(("KETTLEBELL", 1))
        by_name = {evaluation.box.name: evaluation for evaluation in selection.evaluations}
        self.assertEqual(by_name["Small"].status, ITEM_TOO_LARGE)
        self.assertEqual(by_name["Medium"].status, FIT)

    def test_dumbbell_is_too_heavy_for_the_medium_box(self):
        selection = self.recommend(("DUMBBELL", 1))
        by_name = {evaluation.box.name: evaluation for evaluation in selection.evaluations}
        self.assertEqual(by_name["Medium"].status, TOO_HEAVY)
        self.assertEqual(by_name["Large"].status, FIT)

    def test_command_recommends_the_mailer_and_can_save(self):
        output = StringIO()
        call_command("recommend", "PHONE:1", "--save", stdout=output)
        text = output.getvalue()
        self.assertIn("Use Mailer.", text)
        self.assertIn("Saved order", text)
        self.assertEqual(Order.objects.get().recommended_box.name, "Mailer")

    def test_command_rejects_a_bad_token_and_an_unknown_sku(self):
        with self.assertRaises(CommandError):
            call_command("recommend", "PHONE")
        with self.assertRaises(CommandError):
            call_command("recommend", "NOPE:1")
