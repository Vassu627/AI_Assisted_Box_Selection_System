# AI-Assisted Box Selection

When an order is placed, the warehouse needs one shipping box. Each product has a size and a weight. Each box has internal dimensions, a maximum weight, and a cost. This Django project recommends the cheapest box that can actually hold the order.

## Recommendation rule

A box is eligible only when all of the following are true:

1. Every item fits in at least one 90-degree orientation. Items are rigid rectangles. They are not tilted or folded.
2. The total item volume is no larger than the internal volume of the box. This is necessary, and it is not sufficient.
3. The total weight is no heavier than the box allows. An order that weighs exactly the limit still fits.
4. The packer finds a placement where no two items overlap. Faces may touch.

Those checks run in that order. A kettlebell that is both too large and too heavy for a small box is reported as too large, because making it lighter would not make it fit.

Among eligible boxes, the winner is:

1. The lowest cost.
2. If the cost is the same, the smaller internal volume, so the warehouse does not ship extra air.
3. If those are the same, the lower database id, so the result does not flicker between identical records.

A search that stops early is called **not proven**. That box is not recommended. The page says so, instead of claiming the items cannot fit.

Quantity is expanded into separate pieces. Two books are two boxes-within-the-box, not one double-sized book.

The system chooses one box. It does not split an order across several boxes.

## How the packer works

Geometry is converted to integers in hundredths of a centimeter, so `15.50` cm stays exact. Money, weight, and the ranking stay on `Decimal`. Floats are rejected.

The packer tries two steps:

- A greedy pass places the largest remaining item at the first origin that fits, with its stored orientation first. If that succeeds, the placement is checked for overlap and for pieces sticking out of the box.
- If the greedy pass fails and there are at most 8 pieces, a backtracking search tries the other orientations and the other items. Candidate origins are the combinations of `0` and the far faces of items already placed. A packing that can be shifted toward a corner until every item is blocked has its origins in that set.

Past 8 pieces, only the greedy pass is allowed to prove a fit. If it fails, the result is inconclusive. One request also accepts at most 30 pieces, so a web request cannot ask the search to pack a pallet.

This is the case the volume check misses: four `6×6×6` cm cubes have volume 864, and a `10×10×10` cm box has volume 1000, but `6+6` does not fit on any side. The search rejects that box. The same two cubes fit in a `12` cm box, and that more expensive box is recommended when it is the only one that works.

Another case the greedy pass misses: two items stored as `4×3×2` in a `5×4×3` box. The stored orientation fits the first item and then blocks the second. Turning both items to `2×4×3` and sitting them side by side works. The search does that. A test locks the coordinates.

## Project layout

- `catalog` stores products and shipping boxes, including the admin and the demo seed data.
- `fulfillment/packing.py` is the geometry search. It does not import Django models.
- `fulfillment/selector.py` applies weight, cost, volume, and the stable tie-break.
- `fulfillment/services.py` loads active boxes and can save an order.
- The warehouse page, the JSON API, and `manage.py recommend` all call that service.

Inactive boxes stay in the database for old orders and are ignored by new recommendations.

## Setup

Python 3.11 or newer.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/ and enter quantities. The admin is at http://127.0.0.1:8000/admin/.

The development secret key and `DEBUG` are for local use. Set `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=0` before pointing this at a shared network. The warehouse page does not have its own login.

## Demo orders

`seed_demo` loads these products and boxes. The automated tests check each row.

| Order | Box |
| --- | --- |
| PHONE × 1 | Mailer |
| BOOK × 1 | Small |
| MUG × 1 | Small |
| LAPTOP × 1 | Medium |
| KETTLEBELL × 1 | Medium |
| POSTER × 1 | Poster tube |
| DUMBBELL × 1 | Large |
| PHONE × 1 and BOOK × 1 | Small |
| BOOK × 6 | Small |
| DUMBBELL × 1 and KETTLEBELL × 1 | Large |
| POSTER × 1 and PHONE × 1 | Poster tube |
| DUMBBELL × 1, KETTLEBELL × 1, and PHONE × 1 | No box. The order weighs 25.180 kg and the Large box allows 25.000 kg. |

The same check from the command line:

```powershell
.\.venv\Scripts\python.exe manage.py recommend PHONE:1 BOOK:1
.\.venv\Scripts\python.exe manage.py recommend PHONE:1 --save
```

## HTTP API

`POST /api/recommend/` expects JSON and the CSRF token used by the rest of the site.

```json
{
  "save": false,
  "lines": [
    {"sku": "PHONE", "quantity": 1},
    {"sku": "BOOK", "quantity": 1}
  ]
}
```

Duplicate SKUs are added together. `quantity` has to be a JSON integer. `true` is rejected because booleans are integers in Python. `save: true` stores an order, including an order that has no usable box.

`GET /api/products/` and `GET /api/boxes/` list the catalog. Inactive boxes are omitted.

A recommendation looks like this:

For one phone and one book the calculated totals are:

```json
{
  "summary": "Use Small. It costs 1.10 and is the cheapest box that can hold this order.",
  "total_weight_kg": "0.530",
  "total_volume_cm3": "1002.00",
  "order_id": null
}
```

The full payload also has `recommended_box` and `evaluations`. `evaluations` lists every active box, the reason it was kept or rejected, and, for the chosen box, the placement of each piece. X is the box length, Y is the width, and Z is the height, measured from one inner corner.

## Tests

```powershell
.\.venv\Scripts\python.exe manage.py test --verbosity 2
```

The case list is in [TEST_CASES.md](TEST_CASES.md). The output of that command is in [TEST_OUTPUT.md](TEST_OUTPUT.md). The same command runs in GitHub Actions (`.github/workflows/tests.yml`).

The tests cover rotation, touching faces, volume that still cannot be packed, the greedy dead end, cost and size tie-breaks, weight at the exact limit, inactive boxes, the demo orders above, the form, and the JSON API.

## Assumptions

- Dimensions are centimeters to 0.01 cm. Weight is kilograms to 0.001 kg. Cost is a two-decimal amount with no currency code.
- Box dimensions are the internal space. Wall thickness and filler are not modeled.
- There is no carrier dimensional weight, fragility flag, or "this side up" rule.
- One order uses one box.

## AI usage

What was delegated to an AI tool, what was changed, and how the result was checked is in [AI_USAGE.md](AI_USAGE.md).
