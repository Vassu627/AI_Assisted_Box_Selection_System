from django.core.validators import MinValueValidator
from django.db import models


class Order(models.Model):
    """A warehouse request and the box recommendation recorded for it."""

    class Status(models.TextChoices):
        RECOMMENDED = "recommended", "Recommended"
        UNFULFILLABLE = "unfulfillable", "Unfulfillable"

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    recommended_box = models.ForeignKey(
        "catalog.ShippingBox",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    total_weight_kg = models.DecimalField(max_digits=8, decimal_places=3)
    explanation = models.TextField(blank=True)
    evaluation = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.pk} ({self.get_status_display()})"


class OrderLine(models.Model):
    order = models.ForeignKey(Order, related_name="lines", on_delete=models.CASCADE)
    product = models.ForeignKey(
        "catalog.Product",
        related_name="order_lines",
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"],
                name="unique_product_per_order",
            ),
            models.CheckConstraint(
                check=models.Q(quantity__gte=1),
                name="orderline_quantity_at_least_one",
            ),
        ]

    def __str__(self):
        return f"{self.product.sku} × {self.quantity}"
