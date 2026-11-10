import itertools

from django.test import SimpleTestCase

from fulfillment.packing import (
    BoxDims,
    PackItem,
    PackStatus,
    greedy_pack,
    pack,
)


def assert_packed(test, box, items, placements):
    test.assertEqual(
        sorted(placement.index for placement in placements),
        list(range(len(items))),
    )
    for placement in placements:
        test.assertGreaterEqual(placement.x, 0)
        test.assertGreaterEqual(placement.y, 0)
        test.assertGreaterEqual(placement.z, 0)
        test.assertLessEqual(placement.x + placement.l, box.l)
        test.assertLessEqual(placement.y + placement.w, box.w)
        test.assertLessEqual(placement.z + placement.h, box.h)
        item = items[placement.index]
        test.assertEqual(
            tuple(sorted((placement.l, placement.w, placement.h))),
            tuple(sorted((item.l, item.w, item.h))),
        )
    for left, right in itertools.combinations(placements, 2):
        separated = (
            left.x + left.l <= right.x
            or right.x + right.l <= left.x
            or left.y + left.w <= right.y
            or right.y + right.w <= left.y
            or left.z + left.h <= right.z
            or right.z + right.h <= left.z
        )
        test.assertTrue(separated, f"{left} overlaps {right}")


class PackingTests(SimpleTestCase):
    def test_exact_fill(self):
        box = BoxDims(10, 10, 10)
        items = [PackItem("cube", 10, 10, 10)]
        result = pack(box, items)
        self.assertEqual(result.status, PackStatus.FIT)
        self.assertEqual(result.placements[0].l, 10)
        assert_packed(self, box, items, result.placements)

    def test_rotation_is_used_when_the_stored_orientation_does_not_fit(self):
        box = BoxDims(10, 4, 3)
        items = [PackItem("bar", 3, 4, 10)]
        result = pack(box, items)
        self.assertEqual(result.status, PackStatus.FIT)
        placement = result.placements[0]
        self.assertEqual((placement.l, placement.w, placement.h), (10, 4, 3))
        assert_packed(self, box, items, result.placements)

    def test_item_that_is_too_long_in_every_orientation_is_rejected(self):
        result = pack(BoxDims(10, 10, 10), [PackItem("rod", 11, 1, 1)])
        self.assertEqual(result.status, PackStatus.ITEM_TOO_LARGE)
        self.assertEqual(result.offending_labels, ("rod",))

    def test_touching_faces_are_allowed(self):
        box = BoxDims(10, 10, 10)
        items = [PackItem("a", 5, 10, 10), PackItem("b", 5, 10, 10)]
        result = pack(box, items)
        self.assertEqual(result.status, PackStatus.FIT)
        assert_packed(self, box, items, result.placements)

    def test_items_stack_on_the_axis_that_has_room(self):
        box = BoxDims(10, 10, 10)
        items = [PackItem("a", 10, 10, 5), PackItem("b", 10, 10, 5)]
        result = pack(box, items)
        self.assertEqual(result.status, PackStatus.FIT)
        assert_packed(self, box, items, result.placements)

    def test_volume_rejects_before_a_search(self):
        result = pack(BoxDims(10, 10, 10), [PackItem("a", 8, 8, 8), PackItem("b", 8, 8, 8)])
        self.assertEqual(result.status, PackStatus.VOLUME_EXCEEDED)
        self.assertEqual(result.method, "rule")

    def test_four_cubes_that_clear_the_volume_check_still_do_not_pack(self):
        # 4 * 216 = 864, and the box has room for 1000, but 6 + 6 does not fit on any axis.
        items = [PackItem(str(index), 6, 6, 6) for index in range(4)]
        result = pack(BoxDims(10, 10, 10), items)
        self.assertEqual(result.status, PackStatus.CANNOT_PACK)
        self.assertEqual(result.method, "search")

    def test_greedy_commits_to_a_blocking_orientation_and_search_recovers(self):
        box = BoxDims(5, 4, 3)
        items = [PackItem("a", 4, 3, 2), PackItem("b", 4, 3, 2)]
        self.assertIsNone(greedy_pack(box, items))
        result = pack(box, items)
        self.assertEqual(result.status, PackStatus.FIT)
        self.assertEqual(result.method, "search")
        self.assertEqual(
            [(item.index, item.x, item.y, item.z, item.l, item.w, item.h) for item in result.placements],
            [
                (0, 0, 0, 0, 2, 4, 3),
                (1, 2, 0, 0, 2, 4, 3),
            ],
        )
        assert_packed(self, box, items, result.placements)

    def test_same_request_returns_the_same_placement(self):
        box = BoxDims(10, 6, 6)
        items = [PackItem("a", 6, 6, 5), PackItem("b", 6, 6, 5)]
        self.assertEqual(pack(box, items), pack(box, items))

    def test_nine_small_cubes_are_confirmed_by_the_greedy_placer(self):
        box = BoxDims(30, 30, 30)
        items = [PackItem(str(index), 6, 6, 6) for index in range(9)]
        result = pack(box, items)
        self.assertEqual(result.status, PackStatus.FIT)
        self.assertEqual(result.method, "greedy")
        assert_packed(self, box, items, result.placements)

    def test_more_than_eight_items_are_not_called_impossible_when_search_is_skipped(self):
        # One layer can hold 4 cubes of side 6 in this box, so 9 do not fit.
        # The backtracking search is not run past 8 pieces.
        items = [PackItem(str(index), 6, 6, 6) for index in range(9)]
        result = pack(BoxDims(16, 16, 10), items)
        self.assertEqual(result.status, PackStatus.INCONCLUSIVE)

    def test_a_tiny_search_budget_does_not_invent_a_fit(self):
        items = [PackItem("a", 6, 6, 6), PackItem("b", 6, 6, 6)]
        result = pack(BoxDims(12, 12, 12), items, node_limit=1, use_greedy=False)
        self.assertEqual(result.status, PackStatus.INCONCLUSIVE)

    def test_search_proves_two_large_cubes_do_not_fit_within_a_small_budget(self):
        items = [PackItem("a", 6, 6, 6), PackItem("b", 6, 6, 6)]
        result = pack(BoxDims(10, 10, 10), items, node_limit=3, use_greedy=False)
        self.assertEqual(result.status, PackStatus.CANNOT_PACK)
        self.assertLessEqual(result.nodes_used, 3)
