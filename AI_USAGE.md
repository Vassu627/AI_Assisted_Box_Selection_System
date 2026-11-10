# AI Usage Documentation

## 1. Purpose of AI Assistance

AI tools were used as supporting resources during the development of the Box Selection System.

The objective was to use AI for technical discussions, evaluating alternative approaches, identifying potential edge cases, and reviewing implementation quality.

The application architecture, implementation decisions, code modifications, and final verification were reviewed and carried out by me.

AI-generated suggestions were treated as recommendations rather than authoritative solutions.

## 2. AI Tools Used

| Tool                            | Purpose                                                                           |
| ------------------------------- | --------------------------------------------------------------------------------- |
| ChatGPT                         | Problem analysis, algorithm evaluation, architecture discussions, and code review |
| [Other tools, if actually used] | [Actual purpose]                                                                  |

## 3. AI-Assisted Development Activities

The session had one implementation prompt. The later prompt was only to complete this file. Sections 3.1 to 3.5 are the parts of that first answer that were kept, changed, or dropped. They were not five separate chats.

### 3.1 Problem Analysis and System Design

**Objective:** Understand the assignment requirements and identify the core entities, relationships, business constraints, and potential edge cases.

**Prompt used:**

> Python/Django Hiring Assignment: AI-Assisted Box Selection System. We operate an ecommerce platform. When a customer places an order, the warehouse team needs to know which shipping box should be used. Each product has dimensions and weight. Each box has internal dimensions, maximum weight capacity, and cost. Design and build a small Django-based system that recommends the most suitable box for an order. AI use must be recorded in AI_USAGE.md. The submission also needs a README, tests, test output, a chat transcript exported by the author, and a personal note on what was learned. Do not generate that transcript or the learning note with AI.

**Output accepted:**

- Products and shipping boxes are separate catalog records. An order stores the lines and the recommendation that was given.
- The geometry and the cost ranking do not import Django models, so those rules can be tested without a database.
- "Most suitable" means the cheapest box that is proven to hold the order. Equal cost uses the smaller internal volume, then the lower database id.
- One order uses one box. The app says when no box works. It does not split the order.

**Output rejected or modified:**

- Choosing the smallest box and ignoring cost. The assignment includes a cost, so cost is the objective. Volume is only the tie-break.
- A third-party 3D packing library. The reason a box was rejected would have been hidden in the dependency.
- Floats for size, weight, or cost. Values such as 0.10 cm are not exact in binary floating point.

**My decision:**

- `catalog` holds `Product` and `ShippingBox`. `fulfillment` holds `Order`, `OrderLine`, the selector, and the packer.
- Dimensions are centimeters to 0.01 cm. Weight is kilograms to 0.001 kg. Cost has two decimal places and no currency code.
- SQLite is the database. Inactive boxes stay in the database for old orders and are left out of new recommendations.
- Deleting a product or a box that is already on an order is blocked with `PROTECT`.

### 3.2 Box Selection Algorithm

**Objective:** Evaluate approaches for determining whether multiple products can fit inside a shipping box.

**Prompt used:** The assignment prompt in section 3.1. It did not prescribe an algorithm.

**Output accepted:**

- Items are rigid rectangles and may be turned in 90-degree steps. They are not tilted.
- Faces may touch. Overlap is not allowed.
- Quantity is expanded into separate pieces. Two books are two items, not one double-sized book.
- Cheap rejects run before the search, in this order: an item that fits in no orientation, total volume, total weight, then a real placement.
- A greedy pass places the largest item at the first legal origin. If that pass gets stuck, a backtracking search tries other orientations and other items.
- Candidate origins are the combinations of 0 and the far faces of items already placed.
- Geometry is converted to integers in hundredths of a centimeter. The packer checks that a returned fit covers every item, stays inside the box, and is a rotation of the original piece.

**Output rejected or modified:**

- Treating "the volume fits" as proof that the items can be packed. Four 6 cm cubes have volume 864 cm³ and a 10 cm cube has 1000 cm³, but 6 + 6 does not fit on any side.
- A shelf packer as the only check. A miss would have been reported as "does not fit" even when another arrangement worked.
- Checking weight before size. That would have called the kettlebell too heavy for the Small box when 20×20×18 cm also does not fit in 30×22×16 cm. Size is reported first.
- Calling an unfinished search `cannot_pack`. The status is `inconclusive`, and that box is not recommended.

**My decision:**

- The search backtracks only up to 8 pieces, with a budget of 100,000 nodes. Above 8 pieces, only the greedy placement can prove a fit. If it fails, the box is not proven and is not recommended.
- A request may contain at most 30 pieces, and at most 30 of one SKU.
- The packer does not model filler, wall thickness, carrier dimensional weight, or "this side up."

### 3.3 Django Architecture and Code Review

**Objective:** Review the Django implementation for separation of concerns, validation, maintainability, and database design.

**Prompt used:** The assignment prompt in section 3.1.

**Output accepted:**

- `packing.py` answers whether rectangles fit. `selector.py` applies weight, cost, and the tie-break. `services.py` loads active boxes and can save an order.
- The warehouse form, `POST /api/recommend/`, and `manage.py recommend` call that same service.
- Positive sizes are enforced with validators and database check constraints. An order line quantity must be at least 1, and a product appears once per order.
- JSON quantities must be integers. `true` is rejected because a boolean is an integer in Python. Duplicate SKUs in one request are added together.
- Django's CSRF check stays on for the form and the JSON API.

**Output rejected or modified:**

- Django REST framework. The project only needs a few JSON endpoints, so an extra framework was not added.
- `csrf_exempt` on the API, which was considered so that `curl` would work without a token. It was not used.
- Making the recommendation page the only interface. The admin, the command, and the API all remain, and they share one service.

**My decision:**

- The page at `/` is the warehouse screen. `/api/products/`, `/api/boxes/`, and `/api/recommend/` are the JSON endpoints. Inactive boxes are omitted from the page and from `/api/boxes/`.
- Saving an order is optional. An order with no usable box is stored as unfulfillable, with no recommended box.
- The development secret key and `DEBUG` come from the environment. The README says to set both before the app is put on a shared network. The warehouse page has no login of its own.

### 3.4 Testing and Edge Case Analysis

**Objective:** Identify scenarios that could expose incorrect box recommendations.

**Prompt used:** The assignment prompt in section 3.1, which required test cases and saved test output.

**Output accepted:**

- A 10 cm item fills a 10 cm box. Touching faces are allowed. Two 10×10×5 items stack in a 10 cm cube.
- A 3×4×10 item is rotated to 10×4×3 to fit a 10×4×3 box.
- An 11 cm rod does not fit in a 10 cm cube in any orientation.
- Two 8 cm cubes are rejected for volume before any search.
- Four 6 cm cubes are rejected because they cannot be placed, even though their volume fits.
- Two items stored as 4×3×2 in a 5×4×3 box: the greedy pass blocks itself, and the search places both as 2×4×3, one at (0, 0, 0) and the other at (2, 0, 0).
- Nine 6 cm cubes fit in a 30 cm cube by the greedy pass. Nine of the same cubes in a 16×16×10 box are not called impossible, because the backtracking search is not run past 8 pieces.
- A node budget of 1 does not invent a fit. A budget of 3 is enough to prove that two 6 cm cubes do not fit in a 10 cm cube.
- Lower cost beats a smaller box. Equal cost prefers the smaller volume, then the lower id.
- Weight equal to the limit fits. One gram over does not.
- An item that is both too large and too heavy is reported as too large. An order that is both over volume and over weight is reported as over volume.
- The demo orders: one phone uses the Mailer; a phone and a book use Small; the dumbbell uses Large because Medium can hold its size but not its 15 kg; the dumbbell, kettlebell, and phone together weigh 25.180 kg and no box allows that.
- The form rejects a blank order, a negative quantity, and `1.5`. The API rejects an unknown SKU, a boolean quantity, an empty line list, and invalid JSON. `GET /api/recommend/` returns 405.
- `PHONE` quantity 1 plus `PHONE` quantity 2 is saved as quantity 3 and weighs 0.540 kg.

**Output rejected or modified:**

- A draft test used a 4 cm cube and an 8 cm cube and expected "volume exceeded." Their volume is 576 cm³ and the box has 1000 cm³, so the expectation was wrong. The shipped test uses two 8 cm cubes (1024 cm³).
- A draft form test posted `save_order` as an empty string and expected no saved order. The field counts as present whenever it is in the POST body, so that request would have saved an order. The shipped test posts only the quantity.
- The overlap checks in the tests do not call the packer's own helper. They repeat the rule that two items are apart when one far face is at or before the other near face on some axis.

**My decision:**

- Geometry and ranking tests use `SimpleTestCase` and do not touch the database. Demo orders, the command, the form, and the API use Django's `TestCase`.
- The packer also raises if it is about to return a placement that drops an item, sticks out of the box, or is not a rotation of that item.

### 3.5 Performance and Security Review

**Objective:** Evaluate potential performance bottlenecks, API validation, and security concerns.

**Prompt used:** The assignment prompt in section 3.1. It did not ask for a public production deployment.

**Output accepted:**

- The backtracking search stops at 8 pieces and at 100,000 nodes, so one request cannot spend unbounded time proving a hard packing.
- Each line and the whole order are capped at 30 pieces.
- Unknown SKUs, non-integer quantities, zero, and negative quantities are rejected before the packer runs.
- CSRF stays enabled. The development secret is not hardcoded as the only key. `DJANGO_SECRET_KEY` overrides it.

**Output rejected or modified:**

- A login wall on the warehouse page. The assignment is a local tool. The README says to keep it off a public network, or to set `DJANGO_DEBUG=0` and a real secret key before sharing it.
- Disabling CSRF to make the API easier to call with `curl`.
- Running the full item-order search for every large order. Past 8 pieces the result stays inconclusive unless the greedy placement succeeds.

**My decision:**

- Those caps and the CSRF check are the controls that shipped.
- Box and product deletion is blocked when an order still points at the row.

## 4. Mistakes or Limitations Identified in AI Suggestions

1. **The first `manage.py recommend` loop counted a SKU twice and could crash.** It executed `merged[sku] += quantity` before that SKU existed in the dictionary, then added the quantity again. A request would have raised `KeyError` or doubled the count. The loop was rewritten so a SKU is inserted once and then incremented. `test_command_recommends_the_mailer_and_can_save` covers a real command, and the API test checks that two PHONE lines become quantity 3.

2. **The order form bound every quantity input to the whole quantities dictionary.** The page would have shown a dict in the input, and the next submit would reject it as not a whole number. Each product now has `posted_quantity`. `test_phone_form_recommends_the_mailer_without_saving` checks that the phone field is rendered as `1`.

3. **A suggested volume example did not exceed the box.** A 4 cm cube plus an 8 cm cube is 576 cm³, which fits in a 1000 cm³ box. Using that pair as "volume exceeded" would have been a wrong test. Two 8 cm cubes are the case that shipped, including when the order is also heavier than the box, so the test can tell volume from weight.

4. **Weight-before-size was the wrong message when both checks fail.** The kettlebell is over the Small box's weight and also too large for it. Reporting only the weight would stay wrong if the item were lighter. Size and volume are checked first. `test_kettlebell_reports_size_before_weight_on_the_small_box` locks that.

5. **These failure modes were suggested by the assignment's own risk list and were not left in the code.** Volume is not treated as proof of packing. Rotation is tried. Quantity becomes separate pieces. Cost and weight use `Decimal`. A box at its exact weight limit is accepted, and one gram over is rejected.

6. **A Windows PowerShell session rejected `&&` as a command separator.** That was a shell limitation. The same commands were run one at a time. It was not a defect in the Django project.

The test suite then passed on the first run. No assertion was weakened to match a wrong recommendation. The coordinates for the 4×3×2 pair were calculated by hand before that run, and the test matched them.

## 5. Independent Verification

The final implementation was verified through:

- Manual API and form testing against the running development server.
- Django model and business logic tests.
- Boundary-condition testing, including weight equal to the limit and a box filled exactly by one item.
- Invalid input testing.
- Multi-product order testing, including the seeded catalog.
- Weight capacity validation.
- No-suitable-box scenarios, including the dumbbell, kettlebell, and phone together.
- Review of the final source code, which caught the command-loop bug and the form-value bug before the suite was run.

**Actual test execution command:**

```powershell
.\.venv\Scripts\python.exe manage.py test --verbosity 2
```

**Actual test result:**

42 tests, all passing, in 0.335 seconds. `manage.py check` reported no issues during that run. The full terminal output is in [TEST_OUTPUT.md](TEST_OUTPUT.md).

Additional checks outside the suite:

- `python manage.py migrate`, `python manage.py seed_demo`, and `python manage.py recommend PHONE:1 BOOK:1`. The command recommended Small at cost 1.10, rejected the Mailer because the book is 23 cm long, and reported weight 0.530 kg and volume 1002.00 cm3.
- The development server was started on `127.0.0.1:8765`. `GET /` returned 200 and included the product table. `GET /static/css/warehouse.css` returned 200. `GET /api/products/` returned 200 and included PHONE. A form POST for one phone, with the CSRF token and without the save checkbox, returned 200 and the text `Use Mailer.` No browser session was available, so the phone-width layout was not clicked through.

## 6. AI Contribution and Personal Responsibility

AI assistance was used for technical discussions, reviewing alternatives, and identifying potential weaknesses.

The final implementation and engineering decisions were evaluated against the assignment requirements.

I reviewed the suggested approaches, modified unsuitable recommendations, and verified the implemented functionality through testing.

The documented AI interactions represent the actual assistance used during development. The prompts in section 3 are the ones from the Cursor session. The personal "what did you learn" answer and the exported chat transcript are not in this file. Those two parts of the submission have to be written and exported by the author.
