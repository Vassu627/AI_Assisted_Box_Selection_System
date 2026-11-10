"""Turn an API payload or the warehouse form into product lines."""

from fulfillment.limits import MAX_LINE_QUANTITY, MAX_TOTAL_UNITS


def parse_api_payload(payload, products_by_sku):
    """Return (lines, save, errors). lines is a list of (product, quantity)."""

    if not isinstance(payload, dict):
        return [], False, ["Expected a JSON object."]

    save = payload.get("save", False)
    errors = []
    if not isinstance(save, bool):
        errors.append("save must be true or false.")
        save = False

    raw_lines = payload.get("lines")
    if not isinstance(raw_lines, list) or not raw_lines:
        errors.append("Provide at least one line.")
        return [], save, errors

    merged = {}
    order = []
    for entry in raw_lines:
        if not isinstance(entry, dict):
            errors.append("Each line must be an object with sku and quantity.")
            continue
        sku = entry.get("sku")
        quantity = entry.get("quantity")
        if not isinstance(sku, str) or not sku.strip():
            errors.append("Each line needs a sku.")
            continue
        sku = sku.strip()
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            errors.append(f"Quantity for {sku} must be an integer.")
            continue
        if quantity < 1:
            errors.append(f"Quantity for {sku} must be at least 1.")
            continue
        if sku not in merged:
            order.append(sku)
            merged[sku] = 0
        merged[sku] += quantity

    if errors:
        return [], save, errors

    lines = []
    total = 0
    for sku in order:
        quantity = merged[sku]
        if quantity > MAX_LINE_QUANTITY:
            errors.append(f"Quantity for {sku} cannot exceed {MAX_LINE_QUANTITY}.")
            continue
        product = products_by_sku.get(sku)
        if product is None:
            errors.append(f"Unknown sku: {sku}.")
            continue
        lines.append((product, quantity))
        total += quantity

    if not errors and total > MAX_TOTAL_UNITS:
        errors.append(
            f"An order can include at most {MAX_TOTAL_UNITS} items in one box recommendation."
        )
    if errors:
        return [], save, errors
    return lines, save, []


def parse_form(products, post):
    """Return (lines, save, errors, quantities)."""

    quantities = {}
    errors = []
    lines = []
    total = 0
    for product in products:
        raw = post.get(f"qty_{product.id}", "0")
        raw = "0" if raw is None else str(raw).strip()
        if raw == "":
            raw = "0"
        try:
            quantity = int(raw)
        except (TypeError, ValueError):
            quantities[product.id] = 0
            errors.append(f"Quantity for {product.sku} must be a whole number.")
            continue
        quantities[product.id] = quantity
        if quantity < 0:
            errors.append(f"Quantity for {product.sku} cannot be negative.")
            continue
        if quantity > MAX_LINE_QUANTITY:
            errors.append(
                f"Quantity for {product.sku} cannot exceed {MAX_LINE_QUANTITY}."
            )
            continue
        if quantity:
            lines.append((product, quantity))
            total += quantity

    if not errors and total > MAX_TOTAL_UNITS:
        errors.append(
            f"An order can include at most {MAX_TOTAL_UNITS} items in one box recommendation."
        )
    if not errors and not lines:
        errors.append("Enter a quantity for at least one product.")
    if errors:
        lines = []
    return lines, "save_order" in post, errors, quantities
