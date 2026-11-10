"""Orthogonal packing of rectangular items into one rectangular box.

Items may be rotated in 90 degree steps. They may not be tilted, cut, or
stacked so that they overlap. Touching faces is allowed.

Candidate origins are the combinations of coordinates {0} and the far faces
of items already placed. A feasible packing can be shifted toward the origin
until every item is blocked by the wall or by another item, and the search
tries every remaining item at every such point. If that search finishes
without a placement, the items do not fit. If it stops at the node budget,
the result is inconclusive and must not be treated as proof either way.
"""

from dataclasses import dataclass
from enum import Enum
import itertools

# Backtracking is used only up to this many pieces. Larger orders still get
# the greedy placer; if that fails, the result is inconclusive.
EXACT_UNIT_LIMIT = 8
DEFAULT_NODE_LIMIT = 100_000


class PackStatus(str, Enum):
    FIT = "fit"
    ITEM_TOO_LARGE = "item_too_large"
    VOLUME_EXCEEDED = "volume_exceeded"
    CANNOT_PACK = "cannot_pack"
    INCONCLUSIVE = "inconclusive"
    NOT_SEARCHED = "not_searched"


@dataclass(frozen=True, slots=True)
class BoxDims:
    l: int
    w: int
    h: int

    @property
    def volume(self):
        return self.l * self.w * self.h


@dataclass(frozen=True, slots=True)
class PackItem:
    label: str
    l: int
    w: int
    h: int

    @property
    def volume(self):
        return self.l * self.w * self.h


@dataclass(frozen=True, slots=True)
class IntPlacement:
    index: int
    x: int
    y: int
    z: int
    l: int
    w: int
    h: int


@dataclass(frozen=True, slots=True)
class PackResult:
    status: PackStatus
    placements: tuple[IntPlacement, ...] = ()
    offending_labels: tuple[str, ...] = ()
    method: str = "rule"
    nodes_used: int = 0


class SearchBudgetExceeded(Exception):
    def __init__(self, used):
        self.used = used
        super().__init__(f"Search stopped after {used} nodes.")


class Budget:
    def __init__(self, limit):
        if limit < 0:
            raise ValueError("node_limit cannot be negative.")
        self.limit = limit
        self.used = 0

    def tick(self):
        self.used += 1
        if self.used > self.limit:
            raise SearchBudgetExceeded(self.used)


def orientations(item):
    """Stored orientation first, then the other distinct axis permutations."""

    original = (item.l, item.w, item.h)
    others = [
        perm
        for perm in sorted(set(itertools.permutations(original)))
        if perm != original
    ]
    return [original, *others]


def overlaps(left, right):
    if left.x + left.l <= right.x or right.x + right.l <= left.x:
        return False
    if left.y + left.w <= right.y or right.y + right.w <= left.y:
        return False
    if left.z + left.h <= right.z or right.z + right.h <= left.z:
        return False
    return True


def fits_envelope(item, box):
    return any(
        length <= box.l and width <= box.w and height <= box.h
        for length, width, height in orientations(item)
    )


def candidate_origins(placed, box, length, width, height):
    xs = {0}
    ys = {0}
    zs = {0}
    for item in placed:
        xs.add(item.x + item.l)
        ys.add(item.y + item.w)
        zs.add(item.z + item.h)

    origins = []
    for z in sorted(value for value in zs if value + height <= box.h):
        for y in sorted(value for value in ys if value + width <= box.w):
            for x in sorted(value for value in xs if value + length <= box.l):
                if _strictly_inside(placed, x, y, z):
                    continue
                origins.append((x, y, z))
    return origins


def _strictly_inside(placed, x, y, z):
    return any(
        item.x < x < item.x + item.l
        and item.y < y < item.y + item.w
        and item.z < z < item.z + item.h
        for item in placed
    )


def _ensure_valid(box, items, placed):
    if sorted(placement.index for placement in placed) != list(range(len(items))):
        raise RuntimeError("Packer returned a placement that does not cover every item.")
    for placement in placed:
        if min(placement.l, placement.w, placement.h) <= 0:
            raise RuntimeError("Packer returned a non-positive item size.")
        if placement.x < 0 or placement.y < 0 or placement.z < 0:
            raise RuntimeError("Packer returned a placement outside the box.")
        if (
            placement.x + placement.l > box.l
            or placement.y + placement.w > box.w
            or placement.z + placement.h > box.h
        ):
            raise RuntimeError("Packer returned a placement that sticks out of the box.")
        item = items[placement.index]
        if tuple(sorted((placement.l, placement.w, placement.h))) != tuple(
            sorted((item.l, item.w, item.h))
        ):
            raise RuntimeError("Packer returned a placement that is not a rotation of the item.")
    for left, right in itertools.combinations(placed, 2):
        if overlaps(left, right):
            raise RuntimeError("Packer returned overlapping items.")


def greedy_pack(box, items):
    """Place larger items first at the first origin that fits. No backtracking."""

    order = sorted(
        range(len(items)),
        key=lambda index: (
            items[index].volume,
            max(items[index].l, items[index].w, items[index].h),
            -index,
        ),
        reverse=True,
    )
    placed = []
    for index in order:
        item = items[index]
        chosen = None
        for length, width, height in orientations(item):
            if length > box.l or width > box.w or height > box.h:
                continue
            for x, y, z in candidate_origins(placed, box, length, width, height):
                candidate = IntPlacement(index, x, y, z, length, width, height)
                if any(overlaps(candidate, other) for other in placed):
                    continue
                chosen = candidate
                break
            if chosen is not None:
                break
        if chosen is None:
            return None
        placed.append(chosen)
    return tuple(sorted(placed, key=lambda placement: placement.index))


def _item_order_key(items, index):
    item = items[index]
    return (
        item.volume,
        max(item.l, item.w, item.h),
        item.l,
        item.w,
        item.h,
        -index,
    )


def exact_search(box, items, budget):
    def rec(remaining, placed):
        budget.tick()
        if not remaining:
            return placed

        seen_shapes = set()
        ordered = sorted(
            remaining,
            key=lambda item_index: _item_order_key(items, item_index),
            reverse=True,
        )
        for index in ordered:
            item = items[index]
            signature = tuple(sorted((item.l, item.w, item.h)))
            if signature in seen_shapes:
                continue
            seen_shapes.add(signature)
            for length, width, height in orientations(item):
                if length > box.l or width > box.w or height > box.h:
                    continue
                for x, y, z in candidate_origins(placed, box, length, width, height):
                    candidate = IntPlacement(index, x, y, z, length, width, height)
                    if any(overlaps(candidate, other) for other in placed):
                        continue
                    found = rec(remaining - {index}, placed + (candidate,))
                    if found is not None:
                        return found
        return None

    found = rec(frozenset(range(len(items))), ())
    if found is None:
        return None
    return tuple(sorted(found, key=lambda placement: placement.index))


def pack(box, items, *, node_limit=DEFAULT_NODE_LIMIT, use_greedy=True, search=True):
    if box.l <= 0 or box.w <= 0 or box.h <= 0:
        raise ValueError("Box dimensions must be positive.")
    for item in items:
        if item.l <= 0 or item.w <= 0 or item.h <= 0:
            raise ValueError(f"{item.label} has a non-positive dimension.")

    if not items:
        return PackResult(status=PackStatus.FIT, method="rule")

    offenders = tuple(item.label for item in items if not fits_envelope(item, box))
    if offenders:
        return PackResult(
            status=PackStatus.ITEM_TOO_LARGE,
            offending_labels=offenders,
            method="rule",
        )

    if sum(item.volume for item in items) > box.volume:
        return PackResult(status=PackStatus.VOLUME_EXCEEDED, method="rule")

    if not search:
        return PackResult(status=PackStatus.NOT_SEARCHED, method="rule")

    if use_greedy:
        greedy = greedy_pack(box, items)
        if greedy is not None:
            _ensure_valid(box, items, greedy)
            return PackResult(status=PackStatus.FIT, placements=greedy, method="greedy")

    if len(items) > EXACT_UNIT_LIMIT:
        return PackResult(status=PackStatus.INCONCLUSIVE, method="search")

    budget = Budget(node_limit)
    try:
        found = exact_search(box, items, budget)
    except SearchBudgetExceeded:
        return PackResult(
            status=PackStatus.INCONCLUSIVE,
            method="search",
            nodes_used=budget.used,
        )

    if found is None:
        return PackResult(
            status=PackStatus.CANNOT_PACK,
            method="search",
            nodes_used=budget.used,
        )

    _ensure_valid(box, items, found)
    return PackResult(
        status=PackStatus.FIT,
        placements=found,
        method="search",
        nodes_used=budget.used,
    )
