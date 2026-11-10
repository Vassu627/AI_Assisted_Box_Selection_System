from django.contrib import admin

from fulfillment.models import Order, OrderLine


class OrderLineInline(admin.TabularInline):
    model = OrderLine
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "status", "recommended_box", "total_weight_kg")
    list_filter = ("status",)
    readonly_fields = ("created_at", "explanation", "evaluation")
    inlines = [OrderLineInline]
