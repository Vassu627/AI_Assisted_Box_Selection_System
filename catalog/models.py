from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """A shippable product. Dimensions are the packed outer size in centimeters."""

    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    length_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    width_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    height_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )

    class Meta:
        ordering = ["sku"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(length_cm__gt=0)
                    & models.Q(width_cm__gt=0)
                    & models.Q(height_cm__gt=0)
                    & models.Q(weight_kg__gt=0)
                ),
                name="product_positive_measures",
            )
        ]

    def __str__(self):
        return f"{self.sku} — {self.name}"


class ShippingBox(models.Model):
    """A warehouse box. Dimensions are the internal usable space."""

    name = models.CharField(max_length=200, unique=True)
    length_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    width_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    height_cm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    max_weight_kg = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["cost", "name"]
        verbose_name = "shipping box"
        verbose_name_plural = "shipping boxes"
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(length_cm__gt=0)
                    & models.Q(width_cm__gt=0)
                    & models.Q(height_cm__gt=0)
                    & models.Q(max_weight_kg__gt=0)
                    & models.Q(cost__gte=0)
                ),
                name="box_positive_measures",
            )
        ]

    def __str__(self):
        return (
            f"{self.name} ({self.length_cm}×{self.width_cm}×{self.height_cm} cm, "
            f"{self.max_weight_kg} kg, cost {self.cost})"
        )

    @property
    def volume_cm3(self):
        return self.length_cm * self.width_cm * self.height_cm
