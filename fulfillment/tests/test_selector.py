from decimal import Decimal

from django.test import SimpleTestCase

from fulfillment.domain import (
    CANNOT_PACK,
    FIT,
    INCONCLUSIVE,
    ITEM_TOO_LARGE,
    TOO_HEAVY,
    VOLUME_EXCEEDED,
    BoxSpec,
    Unit,
)
from fulfillment.selector import select_box


def unit(**overrides):
    values = {
        "sku": "A",
        "name": "Item",
        "length_cm": Decimal("4"),
        "width_cm": Decimal("4"),
        "height_cm": Decimal("4"),
        "weight_kg": Decimal("1.000"),
        "label": "A",
    }
    values.update(overrides)
    return Unit(**values)


def box(**overrides):
    values = {
        "id": 1,
        "name": "Box",
        "length_cm": Decimal("10"),
        "width_cm": Decimal("10"),
        "height_cm": Decimal("10"),
        "max_weight_kg": Decimal("10.000"),
        "cost": Decimal("1.00"),
    }
    values.update(overrides)
    return BoxSpec(**values)


class SelectorTests(SimpleTestCase):
    def test_lower_cost_beats_a_smaller_box(self):
        small = box(id=1, name="Small", length_cm=Decimal("5"), width_cm=Decimal("5"), height_cm=Decimal("5"), cost=Decimal("5.00"))
        large = box(id=2, name="Large", cost=Decimal("1.00"))
        selection = select_box([unit()], [small, large])
        self.assertEqual(selection.recommended.box.name, "Large")

    def test_equal_cost_prefers_the_smaller_volume(self):
        compact = box(id=1, name="Compact", length_cm=Decimal("6"), width_cm=Decimal("6"), height_cm=Decimal("6"), cost=Decimal("2.00"))
        bulky = box(id=2, name="Bulky", cost=Decimal("2.00"))
        selection = select_box([unit()], [bulky, compact])
        self.assertEqual(selection.recommended.box.name, "Compact")
        self.assertEqual([item.box.name for item in selection.evaluations], ["Compact", "Bulky"])

    def test_equal_cost_and_volume_prefers_the_lower_id(self):
        first = box(id=1, name="First")
        second = box(id=2, name="Second")
        selection = select_box([unit()], [second, first])
        self.assertEqual(selection.recommended.box.id, 1)

    def test_weight_at_the_limit_fits_and_one_gram_over_does_not(self):
        rated = box(max_weight_kg=Decimal("1.000"))
        fits = select_box([unit(weight_kg=Decimal("1.000"))], [rated])
        self.assertEqual(fits.recommended.status, FIT)
        over = select_box([unit(weight_kg=Decimal("1.001"))], [rated])
        self.assertIsNone(over.recommended)
        self.assertEqual(over.evaluations[0].status, TOO_HEAVY)

    def test_size_is_reported_when_the_item_is_also_too_heavy(self):
        selection = select_box(
            [unit(length_cm=Decimal("20"), width_cm=Decimal("20"), height_cm=Decimal("20"), weight_kg=Decimal("50"))],
            [box(max_weight_kg=Decimal("1"))],
        )
        self.assertEqual(selection.evaluations[0].status, ITEM_TOO_LARGE)

    def test_volume_is_reported_when_the_order_is_also_too_heavy(self):
        cubes = [
            unit(label="A", sku="A", length_cm=Decimal("8"), width_cm=Decimal("8"), height_cm=Decimal("8"), weight_kg=Decimal("5")),
            unit(label="B", sku="B", length_cm=Decimal("8"), width_cm=Decimal("8"), height_cm=Decimal("8"), weight_kg=Decimal("5")),
        ]
        selection = select_box(cubes, [box(max_weight_kg=Decimal("1"))])
        self.assertEqual(selection.evaluations[0].status, VOLUME_EXCEEDED)

    def test_a_heavier_box_is_used_when_the_cheap_box_cannot_carry_the_weight(self):
        light = box(id=1, name="Light", max_weight_kg=Decimal("1.000"), cost=Decimal("1.00"))
        strong = box(id=2, name="Strong", max_weight_kg=Decimal("5.000"), cost=Decimal("4.00"))
        selection = select_box([unit(weight_kg=Decimal("2.000"))], [light, strong])
        self.assertEqual(selection.recommended.box.name, "Strong")
        self.assertEqual(selection.evaluations[0].status, TOO_HEAVY)

    def test_an_unpackable_cheap_box_loses_to_a_larger_expensive_box(self):
        cheap = box(id=1, name="Tight", cost=Decimal("1.00"))
        roomy = box(
            id=2,
            name="Roomy",
            length_cm=Decimal("12"),
            width_cm=Decimal("12"),
            height_cm=Decimal("12"),
            cost=Decimal("9.00"),
        )
        cubes = [
            unit(label="A", sku="A", length_cm=Decimal("6"), width_cm=Decimal("6"), height_cm=Decimal("6")),
            unit(label="B", sku="B", length_cm=Decimal("6"), width_cm=Decimal("6"), height_cm=Decimal("6")),
        ]
        selection = select_box(cubes, [cheap, roomy])
        self.assertEqual(selection.recommended.box.name, "Roomy")
        self.assertEqual(selection.evaluations[0].status, CANNOT_PACK)

    def test_low_budget_does_not_recommend_an_unproven_box(self):
        cubes = [
            unit(label="A", sku="A", length_cm=Decimal("6"), width_cm=Decimal("6"), height_cm=Decimal("6")),
            unit(label="B", sku="B", length_cm=Decimal("6"), width_cm=Decimal("6"), height_cm=Decimal("6")),
        ]
        roomy = box(
            name="Roomy",
            length_cm=Decimal("12"),
            width_cm=Decimal("12"),
            height_cm=Decimal("12"),
        )
        selection = select_box(cubes, [roomy], node_limit=1, use_greedy=False)
        self.assertIsNone(selection.recommended)
        self.assertEqual(selection.evaluations[0].status, INCONCLUSIVE)
        self.assertIn("search limit", selection.summary)

    def test_rotation_survives_the_centimeter_conversion(self):
        selection = select_box(
            [unit(length_cm=Decimal("3.00"), width_cm=Decimal("4.00"), height_cm=Decimal("10.00"), label="BAR")],
            [box(name="Flat", length_cm=Decimal("10.00"), width_cm=Decimal("4.00"), height_cm=Decimal("3.00"))],
        )
        placement = selection.recommended.placements[0]
        self.assertEqual(placement.length_cm, Decimal("10.00"))
        self.assertEqual(placement.width_cm, Decimal("4.00"))
        self.assertEqual(placement.height_cm, Decimal("3.00"))

    def test_no_boxes_is_explained(self):
        selection = select_box([unit()], [])
        self.assertIsNone(selection.recommended)
        self.assertEqual(selection.summary, "No shipping boxes are available.")

    def test_empty_order_is_rejected(self):
        with self.assertRaises(ValueError):
            select_box([], [box()])

    def test_float_dimensions_are_rejected(self):
        with self.assertRaises(TypeError):
            select_box([unit(length_cm=1.5)], [box()])
