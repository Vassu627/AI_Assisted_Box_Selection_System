from django.contrib import admin

from catalog.models import Product, ShippingBox


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "length_cm", "width_cm", "height_cm", "weight_kg")
    search_fields = ("sku", "name")


@admin.register(ShippingBox)
class ShippingBoxAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "length_cm",
        "width_cm",
        "height_cm",
        "max_weight_kg",
        "cost",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
