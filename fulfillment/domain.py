"""Plain values shared by the selector, the Django services, and the API."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

FIT = "fit"
TOO_HEAVY = "too_heavy"
ITEM_TOO_LARGE = "item_too_large"
VOLUME_EXCEEDED = "volume_exceeded"
CANNOT_PACK = "cannot_pack"
INCONCLUSIVE = "inconclusive"

STATUS_LABELS = {
    FIT: "Fits",
    TOO_HEAVY: "Too heavy",
    ITEM_TOO_LARGE: "Item too large",
    VOLUME_EXCEEDED: "Volume exceeded",
    CANNOT_PACK: "Cannot pack",
    INCONCLUSIVE: "Not proven",
}


def as_text(value, places):
    quantum = Decimal(places)
    return format(value.quantize(quantum, rounding=ROUND_HALF_UP), "f")


@dataclass(frozen=True, slots=True)
class Unit:
    sku: str
    name: str
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    weight_kg: Decimal
    label: str

    @property
    def volume_cm3(self):
        return self.length_cm * self.width_cm * self.height_cm


@dataclass(frozen=True, slots=True)
class BoxSpec:
    id: int
    name: str
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    max_weight_kg: Decimal
    cost: Decimal

    @property
    def volume_cm3(self):
        return self.length_cm * self.width_cm * self.height_cm


@dataclass(frozen=True, slots=True)
class PlacementView:
    label: str
    x_cm: Decimal
    y_cm: Decimal
    z_cm: Decimal
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal

    def to_dict(self):
        return {
            "label": self.label,
            "x_cm": as_text(self.x_cm, "0.01"),
            "y_cm": as_text(self.y_cm, "0.01"),
            "z_cm": as_text(self.z_cm, "0.01"),
            "length_cm": as_text(self.length_cm, "0.01"),
            "width_cm": as_text(self.width_cm, "0.01"),
            "height_cm": as_text(self.height_cm, "0.01"),
        }


@dataclass(frozen=True, slots=True)
class BoxEvaluation:
    box: BoxSpec
    status: str
    detail: str
    method: str
    placements: tuple[PlacementView, ...] = ()

    @property
    def status_label(self):
        return STATUS_LABELS[self.status]

    def to_dict(self):
        return {
            "box": box_to_dict(self.box),
            "status": self.status,
            "status_label": self.status_label,
            "detail": self.detail,
            "method": self.method,
            "placements": [placement.to_dict() for placement in self.placements],
        }


@dataclass(frozen=True, slots=True)
class Selection:
    total_weight_kg: Decimal
    total_volume_cm3: Decimal
    recommended: BoxEvaluation | None
    evaluations: tuple[BoxEvaluation, ...]
    summary: str

    def to_dict(self):
        return {
            "summary": self.summary,
            "total_weight_kg": as_text(self.total_weight_kg, "0.001"),
            "total_volume_cm3": as_text(self.total_volume_cm3, "0.01"),
            "recommended_box": None if self.recommended is None else self.recommended.to_dict(),
            "evaluations": [evaluation.to_dict() for evaluation in self.evaluations],
        }


def box_to_dict(box):
    return {
        "id": box.id,
        "name": box.name,
        "length_cm": as_text(box.length_cm, "0.01"),
        "width_cm": as_text(box.width_cm, "0.01"),
        "height_cm": as_text(box.height_cm, "0.01"),
        "max_weight_kg": as_text(box.max_weight_kg, "0.001"),
        "cost": as_text(box.cost, "0.01"),
        "volume_cm3": as_text(box.volume_cm3, "0.01"),
    }
