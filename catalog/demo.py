"""Demo catalog used by the seed command and the integration tests.

Box costs rise with size, except the poster tube, which is a shape specialist.
The sizes are chosen so each demo product has an obvious cheapest feasible box.
"""

from decimal import Decimal

from catalog.models import Product, ShippingBox

DEMO_PRODUCTS = [
    {
        "sku": "PHONE",
        "name": "Phone",
        "length_cm": Decimal("15.50"),
        "width_cm": Decimal("7.50"),
        "height_cm": Decimal("1.20"),
        "weight_kg": Decimal("0.180"),
    },
    {
        "sku": "BOOK",
        "name": "Hardcover book",
        "length_cm": Decimal("23.00"),
        "width_cm": Decimal("15.00"),
        "height_cm": Decimal("2.50"),
        "weight_kg": Decimal("0.350"),
    },
    {
        "sku": "MUG",
        "name": "Mug",
        "length_cm": Decimal("12.00"),
        "width_cm": Decimal("9.00"),
        "height_cm": Decimal("10.00"),
        "weight_kg": Decimal("0.400"),
    },
    {
        "sku": "LAPTOP",
        "name": "Laptop",
        "length_cm": Decimal("36.00"),
        "width_cm": Decimal("25.00"),
        "height_cm": Decimal("3.00"),
        "weight_kg": Decimal("2.100"),
    },
    {
        "sku": "KETTLEBELL",
        "name": "Kettlebell",
        "length_cm": Decimal("20.00"),
        "width_cm": Decimal("20.00"),
        "height_cm": Decimal("18.00"),
        "weight_kg": Decimal("10.000"),
    },
    {
        "sku": "POSTER",
        "name": "Rolled poster",
        "length_cm": Decimal("80.00"),
        "width_cm": Decimal("6.00"),
        "height_cm": Decimal("6.00"),
        "weight_kg": Decimal("0.250"),
    },
    {
        "sku": "DUMBBELL",
        "name": "Dumbbell",
        "length_cm": Decimal("32.00"),
        "width_cm": Decimal("15.00"),
        "height_cm": Decimal("15.00"),
        "weight_kg": Decimal("15.000"),
    },
]

DEMO_BOXES = [
    {
        "name": "Mailer",
        "length_cm": Decimal("22.00"),
        "width_cm": Decimal("16.00"),
        "height_cm": Decimal("4.00"),
        "max_weight_kg": Decimal("1.000"),
        "cost": Decimal("0.40"),
    },
    {
        "name": "Small",
        "length_cm": Decimal("30.00"),
        "width_cm": Decimal("22.00"),
        "height_cm": Decimal("16.00"),
        "max_weight_kg": Decimal("5.000"),
        "cost": Decimal("1.10"),
    },
    {
        "name": "Poster tube",
        "length_cm": Decimal("85.00"),
        "width_cm": Decimal("12.00"),
        "height_cm": Decimal("12.00"),
        "max_weight_kg": Decimal("5.000"),
        "cost": Decimal("1.80"),
    },
    {
        "name": "Medium",
        "length_cm": Decimal("45.00"),
        "width_cm": Decimal("35.00"),
        "height_cm": Decimal("25.00"),
        "max_weight_kg": Decimal("12.000"),
        "cost": Decimal("2.00"),
    },
    {
        "name": "Large",
        "length_cm": Decimal("60.00"),
        "width_cm": Decimal("45.00"),
        "height_cm": Decimal("40.00"),
        "max_weight_kg": Decimal("25.000"),
        "cost": Decimal("3.75"),
    },
]


def seed_demo():
    """Create or update the demo products and boxes. Returns (products, boxes)."""

    for row in DEMO_PRODUCTS:
        sku = row["sku"]
        Product.objects.update_or_create(sku=sku, defaults={key: value for key, value in row.items() if key != "sku"})
    for row in DEMO_BOXES:
        name = row["name"]
        ShippingBox.objects.update_or_create(
            name=name,
            defaults={key: value for key, value in row.items() if key != "name"},
        )
    return len(DEMO_PRODUCTS), len(DEMO_BOXES)
