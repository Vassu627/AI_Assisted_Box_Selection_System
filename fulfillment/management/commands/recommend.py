from django.core.management.base import BaseCommand, CommandError

from catalog.models import Product
from fulfillment.domain import as_text
from fulfillment.limits import MAX_LINE_QUANTITY
from fulfillment.services import recommend_lines, save_recommendation


class Command(BaseCommand):
    help = "Recommend a shipping box. Example: python manage.py recommend PHONE:1 BOOK:2"

    def add_arguments(self, parser):
        parser.add_argument(
            "lines",
            nargs="+",
            help="One or more SKU:quantity pairs, for example PHONE:1 BOOK:2.",
        )
        parser.add_argument(
            "--save",
            action="store_true",
            help="Store the request and the recommendation as an order.",
        )

    def handle(self, *args, **options):
        requested = []
        for token in options["lines"]:
            if token.count(":") != 1:
                raise CommandError(f"Expected SKU:quantity, got {token!r}.")
            sku, raw_quantity = token.split(":")
            sku = sku.strip()
            if not sku:
                raise CommandError(f"Expected SKU:quantity, got {token!r}.")
            try:
                quantity = int(raw_quantity)
            except ValueError as exc:
                raise CommandError(f"Quantity for {sku} must be a whole number.") from exc
            if quantity < 1:
                raise CommandError(f"Quantity for {sku} must be at least 1.")
            requested.append((sku, quantity))

        products = {
            product.sku: product
            for product in Product.objects.filter(sku__in=[sku for sku, _ in requested])
        }
        merged = {}
        order = []
        for sku, quantity in requested:
            if sku not in products:
                raise CommandError(f"Unknown sku: {sku}.")
            if sku not in merged:
                order.append(sku)
                merged[sku] = 0
            merged[sku] += quantity
            if merged[sku] > MAX_LINE_QUANTITY:
                raise CommandError(
                    f"Quantity for {sku} cannot exceed {MAX_LINE_QUANTITY}."
                )

        lines = [(products[sku], merged[sku]) for sku in order]
        try:
            selection = recommend_lines(lines)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if options["save"]:
            saved = save_recommendation(lines, selection)
            self.stdout.write(f"Saved order {saved.id}.")
        self.stdout.write(
            f"Weight {as_text(selection.total_weight_kg, '0.001')} kg. "
            f"Volume {as_text(selection.total_volume_cm3, '0.01')} cm3."
        )
        self.stdout.write(selection.summary)
        for evaluation in selection.evaluations:
            self.stdout.write(
                f"{evaluation.box.name}: {evaluation.status_label}. {evaluation.detail}"
            )
