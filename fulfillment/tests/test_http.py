import json
import re
from decimal import Decimal

from django.test import TestCase

from catalog.demo import seed_demo
from catalog.models import Product, ShippingBox
from fulfillment.models import Order


class EmptyCatalogTests(TestCase):
    def test_page_explains_how_to_load_demo_data(self):
        response = self.client.get("/")
        self.assertContains(response, "seed_demo")


class WarehouseHttpTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_demo()
        ShippingBox.objects.create(
            name="Free mailer",
            length_cm=Decimal("22.00"),
            width_cm=Decimal("16.00"),
            height_cm=Decimal("4.00"),
            max_weight_kg=Decimal("1.000"),
            cost=Decimal("0.00"),
            is_active=False,
        )

    def test_page_lists_products_and_hides_inactive_boxes(self):
        response = self.client.get("/")
        self.assertContains(response, "PHONE")
        self.assertContains(response, "Mailer")
        self.assertNotContains(response, "Free mailer")

    def test_phone_form_recommends_the_mailer_without_saving(self):
        phone = Product.objects.get(sku="PHONE")
        response = self.client.post("/", {f"qty_{phone.id}": "1"})
        self.assertContains(response, "Use Mailer.")
        self.assertEqual(Order.objects.count(), 0)
        match = re.search(
            rf'name="qty_{phone.id}"[\s\S]*?value="(\d+)"',
            response.content.decode(),
        )
        self.assertEqual(match.group(1), "1")

    def test_saving_the_form_stores_the_order(self):
        phone = Product.objects.get(sku="PHONE")
        response = self.client.post("/", {f"qty_{phone.id}": "1", "save_order": "on"})
        self.assertContains(response, "Saved as order #")
        order = Order.objects.get()
        self.assertEqual(order.recommended_box.name, "Mailer")
        self.assertEqual(order.lines.get().product.sku, "PHONE")
        self.assertEqual(order.lines.get().quantity, 1)
        self.assertContains(response, "PHONE×1")

    def test_blank_negative_and_text_quantities_are_rejected(self):
        phone = Product.objects.get(sku="PHONE")
        blank = self.client.post("/", {})
        self.assertContains(blank, "Enter a quantity for at least one product.")
        negative = self.client.post("/", {f"qty_{phone.id}": "-1"})
        self.assertContains(negative, "cannot be negative")
        text = self.client.post("/", {f"qty_{phone.id}": "1.5"})
        self.assertContains(text, "must be a whole number")
        self.assertEqual(Order.objects.count(), 0)

    def test_an_unfulfillable_order_can_be_saved(self):
        quantities = {
            f"qty_{Product.objects.get(sku=sku).id}": "1"
            for sku in ("DUMBBELL", "KETTLEBELL", "PHONE")
        }
        quantities["save_order"] = "on"
        response = self.client.post("/", quantities)
        self.assertContains(response, "No shipping box can hold this order.")
        order = Order.objects.get()
        self.assertEqual(order.status, Order.Status.UNFULFILLABLE)
        self.assertIsNone(order.recommended_box)

    def test_api_recommends_a_phone_mailer(self):
        response = self.client.post(
            "/api/recommend/",
            data=json.dumps({"lines": [{"sku": "PHONE", "quantity": 1}]}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["recommended_box"]["box"]["name"], "Mailer")
        self.assertEqual(body["recommended_box"]["status"], "fit")
        self.assertIsNone(body["order_id"])
        self.assertEqual(Order.objects.count(), 0)

    def test_api_merges_duplicate_skus_and_can_save(self):
        response = self.client.post(
            "/api/recommend/",
            data=json.dumps(
                {
                    "save": True,
                    "lines": [
                        {"sku": "PHONE", "quantity": 1},
                        {"sku": "PHONE", "quantity": 2},
                    ],
                }
            ),
            content_type="application/json",
        )
        body = response.json()
        self.assertEqual(body["total_weight_kg"], "0.540")
        self.assertEqual(body["recommended_box"]["box"]["name"], "Mailer")
        order = Order.objects.get(pk=body["order_id"])
        self.assertEqual(order.lines.get().quantity, 3)

    def test_api_rejects_bad_input(self):
        unknown = self.client.post(
            "/api/recommend/",
            data=json.dumps({"lines": [{"sku": "NOPE", "quantity": 1}]}),
            content_type="application/json",
        )
        self.assertEqual(unknown.status_code, 400)
        self.assertIn("Unknown sku: NOPE.", unknown.json()["errors"])

        flagged = self.client.post(
            "/api/recommend/",
            data=json.dumps({"lines": [{"sku": "PHONE", "quantity": True}]}),
            content_type="application/json",
        )
        self.assertEqual(flagged.status_code, 400)
        self.assertIn("integer", flagged.json()["errors"][0])

        empty = self.client.post(
            "/api/recommend/",
            data=json.dumps({"lines": []}),
            content_type="application/json",
        )
        self.assertEqual(empty.status_code, 400)

        broken = self.client.post(
            "/api/recommend/",
            data="{",
            content_type="application/json",
        )
        self.assertEqual(broken.status_code, 400)
        self.assertEqual(self.client.get("/api/recommend/").status_code, 405)

    def test_catalog_endpoints_hide_inactive_boxes(self):
        products = self.client.get("/api/products/").json()["products"]
        self.assertIn("PHONE", [product["sku"] for product in products])
        boxes = self.client.get("/api/boxes/").json()["boxes"]
        names = [box["name"] for box in boxes]
        self.assertIn("Mailer", names)
        self.assertNotIn("Free mailer", names)
