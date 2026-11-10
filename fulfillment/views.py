import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from catalog.models import Product, ShippingBox
from fulfillment.domain import as_text
from fulfillment.models import Order
from fulfillment.parsing import parse_api_payload, parse_form
from fulfillment.services import recommend_lines, save_recommendation


@require_http_methods(["GET", "POST"])
def recommend_page(request):
    products = list(Product.objects.all())
    boxes = list(ShippingBox.objects.filter(is_active=True))
    errors = []
    selection = None
    saved_order = None
    quantities = {product.id: 0 for product in products}
    save_checked = True

    if request.method == "POST":
        lines, save_checked, errors, quantities = parse_form(products, request.POST)
        if not errors:
            try:
                selection = recommend_lines(lines)
            except ValueError as exc:
                errors = [str(exc)]
            else:
                if save_checked:
                    saved_order = save_recommendation(lines, selection)

    for product in products:
        product.posted_quantity = quantities.get(product.id, 0)

    recent_orders = Order.objects.select_related("recommended_box").prefetch_related(
        "lines__product"
    )[:8]
    return render(
        request,
        "fulfillment/recommend.html",
        {
            "products": products,
            "boxes": boxes,
            "errors": errors,
            "selection": selection,
            "saved_order": saved_order,
            "save_checked": save_checked,
            "recent_orders": recent_orders,
        },
    )


@require_POST
def recommend_api(request):
    if not request.body:
        return JsonResponse({"errors": ["Invalid JSON."]}, status=400)
    try:
        payload = json.loads(request.body.decode())
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"errors": ["Invalid JSON."]}, status=400)

    skus = []
    raw_lines = payload.get("lines") if isinstance(payload, dict) else None
    if isinstance(raw_lines, list):
        for entry in raw_lines:
            if isinstance(entry, dict) and isinstance(entry.get("sku"), str):
                skus.append(entry["sku"].strip())
    products_by_sku = {
        product.sku: product for product in Product.objects.filter(sku__in=skus)
    }
    lines, save, errors = parse_api_payload(payload, products_by_sku)
    if errors:
        return JsonResponse({"errors": errors}, status=400)

    try:
        selection = recommend_lines(lines)
    except ValueError as exc:
        return JsonResponse({"errors": [str(exc)]}, status=400)

    saved = save_recommendation(lines, selection) if save else None
    body = selection.to_dict()
    body["order_id"] = None if saved is None else saved.id
    return JsonResponse(body)


@require_GET
def products_api(request):
    products = [
        {
            "sku": product.sku,
            "name": product.name,
            "length_cm": as_text(product.length_cm, "0.01"),
            "width_cm": as_text(product.width_cm, "0.01"),
            "height_cm": as_text(product.height_cm, "0.01"),
            "weight_kg": as_text(product.weight_kg, "0.001"),
        }
        for product in Product.objects.all()
    ]
    return JsonResponse({"products": products})


@require_GET
def boxes_api(request):
    boxes = [
        {
            "id": box.id,
            "name": box.name,
            "length_cm": as_text(box.length_cm, "0.01"),
            "width_cm": as_text(box.width_cm, "0.01"),
            "height_cm": as_text(box.height_cm, "0.01"),
            "max_weight_kg": as_text(box.max_weight_kg, "0.001"),
            "cost": as_text(box.cost, "0.01"),
            "volume_cm3": as_text(box.volume_cm3, "0.01"),
        }
        for box in ShippingBox.objects.filter(is_active=True)
    ]
    return JsonResponse({"boxes": boxes})
