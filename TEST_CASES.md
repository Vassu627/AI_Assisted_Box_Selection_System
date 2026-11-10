# Test cases

These are the cases the project is graded against. Each one is an automated test. The run that passed all 42 of them is in [TEST_OUTPUT.md](TEST_OUTPUT.md).

```powershell
.\.venv\Scripts\python.exe manage.py test --verbosity 2
```

Sizes are centimeters. Weights are kilograms. Items may be turned in 90-degree steps. The recommended box is the cheapest one that is proven to fit. Equal cost uses the smaller internal volume, then the lower id.

The seeded catalog used by the order cases is:

| Box | Internal cm | Max kg | Cost |
| --- | --- | --- | --- |
| Mailer | 22 × 16 × 4 | 1.000 | 0.40 |
| Small | 30 × 22 × 16 | 5.000 | 1.10 |
| Poster tube | 85 × 12 × 12 | 5.000 | 1.80 |
| Medium | 45 × 35 × 25 | 12.000 | 2.00 |
| Large | 60 × 45 × 40 | 25.000 | 3.75 |

| SKU | Size cm | Weight kg |
| --- | --- | --- |
| PHONE | 15.50 × 7.50 × 1.20 | 0.180 |
| BOOK | 23.00 × 15.00 × 2.50 | 0.350 |
| MUG | 12.00 × 9.00 × 10.00 | 0.400 |
| LAPTOP | 36.00 × 25.00 × 3.00 | 2.100 |
| KETTLEBELL | 20.00 × 20.00 × 18.00 | 10.000 |
| POSTER | 80.00 × 6.00 × 6.00 | 0.250 |
| DUMBBELL | 32.00 × 15.00 × 15.00 | 15.000 |

## 1. Seeded orders

Automated in `fulfillment/tests/test_demo.py`, method `test_catalog_scenarios`.

| ID | Order | Expected box | Why this case exists |
| --- | --- | --- | --- |
| O1 | PHONE × 1 | Mailer | The cheapest box fits a flat light item. |
| O2 | BOOK × 1 | Small | The book is 23 cm long, so the 22 cm Mailer cannot take it. |
| O3 | MUG × 1 | Small | Every side of the mug is longer than the Mailer's 4 cm height. |
| O4 | LAPTOP × 1 | Medium | 36 cm does not fit the Small box or the tube's 12 cm cross-section. |
| O5 | KETTLEBELL × 1 | Medium | Lighter boxes are too small. Large also fits and costs more. |
| O6 | POSTER × 1 | Poster tube | Only the tube has a side of at least 80 cm. |
| O7 | DUMBBELL × 1 | Large | Medium can hold 32 × 15 × 15 cm, but 15 kg is over its 12 kg limit. |
| O8 | PHONE × 1, BOOK × 1 | Small | The book eliminates the Mailer. Both items fit in Small. |
| O9 | BOOK × 6 | Small | Six books stack to 15 cm, which is inside the Small box's 16 cm height. Weight is 2.100 kg. |
| O10 | DUMBBELL × 1, KETTLEBELL × 1 | Large | Combined weight is exactly 25.000 kg, the Large limit. |
| O11 | POSTER × 1, PHONE × 1 | Poster tube | The phone has to sit beside the poster inside the tube. |
| O12 | DUMBBELL × 1, KETTLEBELL × 1, PHONE × 1 | No box | Combined weight is 25.180 kg. Large allows 25.000 kg. |

| ID | Input | Expected | Test |
| --- | --- | --- | --- |
| O13 | KETTLEBELL against Small | Status `item_too_large`, not `too_heavy`. Medium is `fit`. | `test_kettlebell_reports_size_before_weight_on_the_small_box` |
| O14 | DUMBBELL against Medium | Status `too_heavy`. Large is `fit`. | `test_dumbbell_is_too_heavy_for_the_medium_box` |
| O15 | `seed_demo` run twice | Still 7 products and 5 boxes. | `test_seed_is_idempotent` |

The same orders can be checked by hand after `python manage.py seed_demo`:

```powershell
.\.venv\Scripts\python.exe manage.py recommend PHONE:1
.\.venv\Scripts\python.exe manage.py recommend PHONE:1 BOOK:1
.\.venv\Scripts\python.exe manage.py recommend DUMBBELL:1 KETTLEBELL:1 PHONE:1
```

O1 prints `Use Mailer.` O8 prints `Use Small.` O12 prints `No shipping box can hold this order.`

## 2. Ranking and weight

Automated in `fulfillment/tests/test_selector.py`. Boxes below are not the seeded catalog. They are built for the single rule under test.

| ID | Input | Expected | Test |
| --- | --- | --- | --- |
| R1 | A 4 cm cube. A 5 cm box costs 5.00. A 10 cm box costs 1.00. | The 10 cm box. Lower cost beats the smaller box. | `test_lower_cost_beats_a_smaller_box` |
| R2 | Same item. A 6 cm box and a 10 cm box both cost 2.00. | The 6 cm box. Equal cost uses the smaller volume. | `test_equal_cost_prefers_the_smaller_volume` |
| R3 | Two boxes with the same size and the same cost. Ids 1 and 2. | Id 1. | `test_equal_cost_and_volume_prefers_the_lower_id` |
| R4 | Item weight 1.000 kg. Box limit 1.000 kg. | Fit. | `test_weight_at_the_limit_fits_and_one_gram_over_does_not` |
| R5 | Same box. Item weight 1.001 kg. | No box. Status `too_heavy`. | same test |
| R6 | A 20 cm cube weighing 50 kg. A 10 cm box limited to 1 kg. | `item_too_large`, even though it is also too heavy. | `test_size_is_reported_when_the_item_is_also_too_heavy` |
| R7 | Two 8 cm cubes, 5 kg each. A 10 cm box limited to 1 kg. Volume is 1024 cm³ against 1000 cm³. | `volume_exceeded`, even though it is also too heavy. | `test_volume_is_reported_when_the_order_is_also_too_heavy` |
| R8 | A 2 kg item. A cheap box allows 1 kg. A costlier box allows 5 kg. Both are large enough. | The costlier box. | `test_a_heavier_box_is_used_when_the_cheap_box_cannot_carry_the_weight` |
| R9 | Two 6 cm cubes. A 10 cm box costs 1.00. A 12 cm box costs 9.00. | The 12 cm box. The cheap box is `cannot_pack` because 6 + 6 does not fit on a 10 cm side. | `test_an_unpackable_cheap_box_loses_to_a_larger_expensive_box` |
| R10 | Two 6 cm cubes in a 12 cm box, search budget of 1 node, greedy pass off. | No recommendation. Status `inconclusive`. | `test_low_budget_does_not_recommend_an_unproven_box` |
| R11 | A 3.00 × 4.00 × 10.00 cm item in a 10.00 × 4.00 × 3.00 cm box. | Fit, placed as 10.00 × 4.00 × 3.00 cm. | `test_rotation_survives_the_centimeter_conversion` |
| R12 | One valid item and an empty box list. | Summary `No shipping boxes are available.` | `test_no_boxes_is_explained` |
| R13 | An empty item list. | `ValueError`. | `test_empty_order_is_rejected` |
| R14 | A length passed as the float `1.5`. | `TypeError`. Dimensions must be `Decimal`. | `test_float_dimensions_are_rejected` |

## 3. Packing geometry

Automated in `fulfillment/tests/test_packing.py`. Dimensions here are integer centimeters inside the packer.

| ID | Input | Expected | Test |
| --- | --- | --- | --- |
| P1 | One 10×10×10 item in a 10×10×10 box. | Fit. The placement fills the box. | `test_exact_fill` |
| P2 | Item stored as 3×4×10 in a 10×4×3 box. | Fit only after rotation, placed as 10×4×3. | `test_rotation_is_used_when_the_stored_orientation_does_not_fit` |
| P3 | An 11×1×1 rod in a 10×10×10 box. | `item_too_large`. | `test_item_that_is_too_long_in_every_orientation_is_rejected` |
| P4 | Two 5×10×10 items in a 10×10×10 box. | Fit. Their faces may touch. | `test_touching_faces_are_allowed` |
| P5 | Two 10×10×5 items in a 10×10×10 box. | Fit, stacked. | `test_items_stack_on_the_axis_that_has_room` |
| P6 | Two 8×8×8 items in a 10×10×10 box. | `volume_exceeded` before any search. | `test_volume_rejects_before_a_search` |
| P7 | Four 6×6×6 items in a 10×10×10 box. Volume 864 of 1000. | `cannot_pack`. | `test_four_cubes_that_clear_the_volume_check_still_do_not_pack` |
| P8 | Two items stored as 4×3×2 in a 5×4×3 box. | The greedy pass returns nothing. The search fits them as 2×4×3 at (0,0,0) and (2,0,0). | `test_greedy_commits_to_a_blocking_orientation_and_search_recovers` |
| P9 | Two 6×6×5 items in a 10×6×6 box, packed twice. | The two results are identical. | `test_same_request_returns_the_same_placement` |
| P10 | Nine 6×6×6 items in a 30×30×30 box. | Fit by the greedy pass. Every placement stays inside and does not overlap. | `test_nine_small_cubes_are_confirmed_by_the_greedy_placer` |
| P11 | Nine 6×6×6 items in a 16×16×10 box. One layer holds only four. | `inconclusive`. Past 8 pieces a failed greedy pass is not reported as proof that packing is impossible. | `test_more_than_eight_items_are_not_called_impossible_when_search_is_skipped` |
| P12 | Two 6 cm cubes in a 12 cm box. Budget 1. Greedy pass off. | `inconclusive`. The budget must not invent a fit. | `test_a_tiny_search_budget_does_not_invent_a_fit` |
| P13 | Two 6 cm cubes in a 10 cm box. Budget 3. Greedy pass off. | `cannot_pack`, using no more than 3 nodes. | `test_search_proves_two_large_cubes_do_not_fit_within_a_small_budget` |

For every fit in this group, the test also checks that each placement is a rotation of its item, lies inside the box, and does not overlap another item. That check is separate from the packer's own overlap function.

## 4. Warehouse page, API, and command

Automated in `fulfillment/tests/test_http.py` and `fulfillment/tests/test_demo.py`. The HTTP cases seed the catalog and add an inactive box named Free mailer: same size as the Mailer, cost 0.00.

| ID | Input | Expected | Test |
| --- | --- | --- | --- |
| H1 | `GET /` with an empty catalog. | Page tells the operator to run `seed_demo`. | `test_page_explains_how_to_load_demo_data` |
| H2 | `GET /` after seeding. | PHONE and Mailer are shown. Free mailer is not. | `test_page_lists_products_and_hides_inactive_boxes` |
| H3 | Form POST, PHONE quantity 1, save unchecked. | Page says `Use Mailer.` No order row is created. The phone field is redisplayed as 1. | `test_phone_form_recommends_the_mailer_without_saving` |
| H4 | Same POST with save checked. | Order is stored with box Mailer, line PHONE × 1, and the recent-order list shows `PHONE×1`. | `test_saving_the_form_stores_the_order` |
| H5 | Form POST with no quantities, then quantity -1, then quantity `1.5`. | Errors: at least one product, cannot be negative, must be a whole number. No order is stored. | `test_blank_negative_and_text_quantities_are_rejected` |
| H6 | Form POST for DUMBBELL, KETTLEBELL, and PHONE, save checked. | `No shipping box can hold this order.` The order is saved with status unfulfillable and a null box. | `test_an_unfulfillable_order_can_be_saved` |
| H7 | `POST /api/recommend/` with `{"lines":[{"sku":"PHONE","quantity":1}]}`. | HTTP 200. Recommended box name Mailer, status `fit`, `order_id` null. | `test_api_recommends_a_phone_mailer` |
| H8 | API lines PHONE 1 and PHONE 2, `save: true`. | Weight `0.540`. Box Mailer. Saved line quantity is 3. | `test_api_merges_duplicate_skus_and_can_save` |
| H9 | API SKU `NOPE`. | HTTP 400. Error contains `Unknown sku: NOPE.` | `test_api_rejects_bad_input` |
| H10 | API quantity `true`. | HTTP 400. The error says the quantity must be an integer. | same test |
| H11 | API `"lines": []`. | HTTP 400. | same test |
| H12 | API body `{`. | HTTP 400. | same test |
| H13 | `GET /api/recommend/`. | HTTP 405. | same test |
| H14 | `GET /api/products/` and `GET /api/boxes/`. | PHONE is in the product list. Mailer is in the box list. Free mailer is not. | `test_catalog_endpoints_hide_inactive_boxes` |
| H15 | `manage.py recommend PHONE:1 --save`. | Output contains `Use Mailer.` and `Saved order`. The stored box is Mailer. | `test_command_recommends_the_mailer_and_can_save` |
| H16 | `manage.py recommend PHONE` and `manage.py recommend NOPE:1`. | Both raise `CommandError`. | `test_command_rejects_a_bad_token_and_an_unknown_sku` |

## Result

`python manage.py test --verbosity 2` ran these cases on 10 November 2026: 42 tests, all passing, in 0.335 seconds. The terminal log is [TEST_OUTPUT.md](TEST_OUTPUT.md).
