"""Choose the cheapest box that is proven to hold the order.

A box is rejected when an item cannot be rotated into it, when the items
need more volume than the box has, or when the order is heavier than the
box allows. Those checks run before the placement search. Among boxes with
a proven placement, the winner is:

1. Lower box cost.
2. Smaller internal volume, so an equal price does not ship extra air.
3. Lower id, so two identical records have a stable winner.

An inconclusive search is not a recommendation.
"""

from decimal import Decimal, ROUND_HALF_UP

from fulfillment.domain import (
    CANNOT_PACK,
    FIT,
    INCONCLUSIVE,
    ITEM_TOO_LARGE,
    TOO_HEAVY,
    VOLUME_EXCEEDED,
    BoxEvaluation,
    PlacementView,
    Selection,
    as_text,
)
from fulfillment.packing import (
    DEFAULT_NODE_LIMIT,
    BoxDims,
    PackItem,
    PackStatus,
    pack,
)

SCALE = Decimal(100)
_STATUS_BY_PACK = {
    PackStatus.FIT: FIT,
    PackStatus.ITEM_TOO_LARGE: ITEM_TOO_LARGE,
    PackStatus.VOLUME_EXCEEDED: VOLUME_EXCEEDED,
    PackStatus.CANNOT_PACK: CANNOT_PACK,
    PackStatus.INCONCLUSIVE: INCONCLUSIVE,
}


def select_box(units, boxes, *, node_limit=DEFAULT_NODE_LIMIT, use_greedy=True):
    if not units:
        raise ValueError("Add at least one item.")
    _validate_units(units)
    _validate_boxes(boxes)

    total_weight = sum((unit.weight_kg for unit in units), Decimal("0"))
    total_weight = total_weight.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    total_volume = sum((unit.volume_cm3 for unit in units), Decimal("0"))
    pack_items = tuple(_pack_item(unit) for unit in units)

    ranked_boxes = sorted(boxes, key=lambda box: (box.cost, box.volume_cm3, box.id))
    evaluations = tuple(
        _evaluate_box(units, pack_items, box, total_weight, node_limit, use_greedy)
        for box in ranked_boxes
    )
    recommended = next((evaluation for evaluation in evaluations if evaluation.status == FIT), None)
    return Selection(
        total_weight_kg=total_weight,
        total_volume_cm3=total_volume,
        recommended=recommended,
        evaluations=evaluations,
        summary=_summary(recommended, evaluations, ranked_boxes),
    )


def _validate_units(units):
    for unit in units:
        for value, field in (
            (unit.length_cm, "length"),
            (unit.width_cm, "width"),
            (unit.height_cm, "height"),
            (unit.weight_kg, "weight"),
        ):
            if isinstance(value, float) or not isinstance(value, Decimal):
                raise TypeError(f"{unit.label} {field} must be a Decimal, not {type(value).__name__}.")
            if value <= 0:
                raise ValueError(f"{unit.label} has a non-positive {field}.")
        if centimeters_to_units(unit.length_cm) <= 0:
            raise ValueError(f"{unit.label} length rounds to zero at 0.01 cm.")
        if centimeters_to_units(unit.width_cm) <= 0:
            raise ValueError(f"{unit.label} width rounds to zero at 0.01 cm.")
        if centimeters_to_units(unit.height_cm) <= 0:
            raise ValueError(f"{unit.label} height rounds to zero at 0.01 cm.")


def _validate_boxes(boxes):
    for box in boxes:
        for value, field in (
            (box.length_cm, "length"),
            (box.width_cm, "width"),
            (box.height_cm, "height"),
            (box.max_weight_kg, "max weight"),
            (box.cost, "cost"),
        ):
            if isinstance(value, float) or not isinstance(value, Decimal):
                raise TypeError(f"{box.name} {field} must be a Decimal, not {type(value).__name__}.")
        if box.length_cm <= 0 or box.width_cm <= 0 or box.height_cm <= 0 or box.max_weight_kg <= 0:
            raise ValueError(f"{box.name} has a non-positive size or weight limit.")
        if box.cost < 0:
            raise ValueError(f"{box.name} has a negative cost.")


def centimeters_to_units(value):
    scaled = value * SCALE
    if scaled != scaled.to_integral_value():
        scaled = scaled.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(scaled)


def units_to_centimeters(value):
    return (Decimal(value) / SCALE).quantize(Decimal("0.01"))


def _pack_item(unit):
    return PackItem(
        label=unit.label,
        l=centimeters_to_units(unit.length_cm),
        w=centimeters_to_units(unit.width_cm),
        h=centimeters_to_units(unit.height_cm),
    )


def _evaluate_box(units, pack_items, box, total_weight, node_limit, use_greedy):
    box_dims = BoxDims(
        centimeters_to_units(box.length_cm),
        centimeters_to_units(box.width_cm),
        centimeters_to_units(box.height_cm),
    )
    # Size rejects come before weight. A box that cannot hold the pieces is
    # still the wrong box if the order is also lighter.
    preview = pack(box_dims, pack_items, search=False)
    if preview.status is not PackStatus.NOT_SEARCHED:
        return _from_pack(units, box, preview)

    if total_weight > box.max_weight_kg:
        return BoxEvaluation(
            box=box,
            status=TOO_HEAVY,
            detail=(
                f"The order weighs {as_text(total_weight, '0.001')} kg and "
                f"{box.name} allows {as_text(box.max_weight_kg, '0.001')} kg."
            ),
            method="rule",
        )

    result = pack(
        box_dims,
        pack_items,
        node_limit=node_limit,
        use_greedy=use_greedy,
    )
    return _from_pack(units, box, result)


def _from_pack(units, box, result):
    status = _STATUS_BY_PACK[result.status]
    return BoxEvaluation(
        box=box,
        status=status,
        detail=_detail(units, box, status, result),
        method=result.method,
        placements=_placement_views(units, result.placements),
    )


def _detail(units, box, status, result):
    if status == TOO_HEAVY:
        raise RuntimeError("Weight details are built before packing.")
    if status == ITEM_TOO_LARGE:
        labels = set(result.offending_labels)
        offenders = [unit for unit in units if unit.label in labels]
        if len(offenders) == 1:
            rendered = _unit_size(offenders[0])
            verb = "does"
        else:
            rendered = "; ".join(_unit_size(unit) for unit in offenders)
            verb = "do"
        return f"{rendered} {verb} not fit in {_box_size(box)} in any orientation."
    if status == VOLUME_EXCEEDED:
        item_volume = sum((unit.volume_cm3 for unit in units), Decimal("0"))
        return (
            f"The items occupy {as_text(item_volume, '0.01')} cm³ and "
            f"{box.name} has {as_text(box.volume_cm3, '0.01')} cm³ inside."
        )
    if status == CANNOT_PACK:
        return (
            f"Each item fits in {box.name} and the total volume fits, "
            "but the items cannot be placed without overlapping."
        )
    if status == INCONCLUSIVE:
        return (
            f"The search did not prove whether the items fit in {box.name}. "
            "This box was not recommended."
        )
    return (
        f"The items fit. Cost {as_text(box.cost, '0.01')}. "
        f"Internal volume {as_text(box.volume_cm3, '0.01')} cm³."
    )


def _unit_size(unit):
    return (
        f"{unit.label} ("
        f"{as_text(unit.length_cm, '0.01')} × "
        f"{as_text(unit.width_cm, '0.01')} × "
        f"{as_text(unit.height_cm, '0.01')} cm)"
    )


def _box_size(box):
    return (
        f"{box.name} ("
        f"{as_text(box.length_cm, '0.01')} × "
        f"{as_text(box.width_cm, '0.01')} × "
        f"{as_text(box.height_cm, '0.01')} cm)"
    )


def _placement_views(units, placements):
    views = []
    for placement in placements:
        unit = units[placement.index]
        views.append(
            PlacementView(
                label=unit.label,
                x_cm=units_to_centimeters(placement.x),
                y_cm=units_to_centimeters(placement.y),
                z_cm=units_to_centimeters(placement.z),
                length_cm=units_to_centimeters(placement.l),
                width_cm=units_to_centimeters(placement.w),
                height_cm=units_to_centimeters(placement.h),
            )
        )
    return tuple(views)


def _summary(recommended, evaluations, boxes):
    if not boxes:
        return "No shipping boxes are available."
    if recommended is not None:
        box = recommended.box
        return (
            f"Use {box.name}. It costs {as_text(box.cost, '0.01')} and is the "
            "cheapest box that can hold this order."
        )
    if any(evaluation.status == INCONCLUSIVE for evaluation in evaluations):
        return (
            "No box was proven to hold this order. "
            "At least one box was not fully checked within the search limit."
        )
    return "No shipping box can hold this order."
