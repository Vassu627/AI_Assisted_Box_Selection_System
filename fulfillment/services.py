"""Django adapter around the pure box selector."""

from django.db import transaction

from catalog.models import ShippingBox
from fulfillment.domain import BoxSpec, Unit
from fulfillment.limits import MAX_LINE_QUANTITY, MAX_TOTAL_UNITS
from fulfillment.models import Order, OrderLine
from fulfillment.selector import select_box


def recommend_lines(lines, **selector_options):
    """Recommend a box for (product, quantity) lines. Raises ValueError on bad input."""

    if not lines:
        raise ValueError("Add at least one item.")

    total = 0
    for product, quantity in lines:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError(f"Quantity for {product.sku} must be at least 1.")
        if quantity > MAX_LINE_QUANTITY:
            raise ValueError(
                f"Quantity for {product.sku} cannot exceed {MAX_LINE_QUANTITY}."
            )
        total += quantity
    if total > MAX_TOTAL_UNITS:
        raise ValueError(
            f"An order can include at most {MAX_TOTAL_UNITS} items in one box recommendation."
        )

    units = expand_lines(lines)
    boxes = [
        box_spec_from_model(box)
        for box in ShippingBox.objects.filter(is_active=True)
    ]
    return select_box(units, boxes, **selector_options)


def save_recommendation(lines, selection):
    with transaction.atomic():
        recommended_id = None
        if selection.recommended is not None:
            recommended_id = selection.recommended.box.id
        order = Order.objects.create(
            status=(
                Order.Status.RECOMMENDED
                if selection.recommended is not None
                else Order.Status.UNFULFILLABLE
            ),
            recommended_box_id=recommended_id,
            total_weight_kg=selection.total_weight_kg,
            explanation=selection.summary,
            evaluation=selection.to_dict(),
        )
        OrderLine.objects.bulk_create(
            [
                OrderLine(order=order, product=product, quantity=quantity)
                for product, quantity in lines
            ]
        )
    return order


def expand_lines(lines):
    units = []
    for product, quantity in lines:
        for number in range(1, quantity + 1):
            label = product.sku if quantity == 1 else f"{product.sku} #{number}"
            units.append(
                Unit(
                    sku=product.sku,
                    name=product.name,
                    length_cm=product.length_cm,
                    width_cm=product.width_cm,
                    height_cm=product.height_cm,
                    weight_kg=product.weight_kg,
                    label=label,
                )
            )
    return units


def box_spec_from_model(box):
    return BoxSpec(
        id=box.id,
        name=box.name,
        length_cm=box.length_cm,
        width_cm=box.width_cm,
        height_cm=box.height_cm,
        max_weight_kg=box.max_weight_kg,
        cost=box.cost,
    )
