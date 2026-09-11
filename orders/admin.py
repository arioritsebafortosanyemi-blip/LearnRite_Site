from django.contrib import admin
from django.utils import timezone

from orders.emails import send_pickup_ready_notification
from orders.models import BulkDiscountRule, Cart, CartItem, Coupon, Order, OrderItem, PaymentAccount


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("book", "title", "unit_price", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_reference", "full_name", "email", "delivery_method", "status", "total", "created_at")
    list_filter = ("status", "delivery_method")
    search_fields = ("order_reference", "full_name", "email", "phone_number")
    readonly_fields = ("order_reference", "user", "email", "full_name", "phone_number", "delivery_method",
                       "shipping_address", "subtotal", "discount_amount", "coupon",
                       "coupon_discount_amount", "total", "created_at")
    inlines = [OrderItemInline]

    def save_model(self, request, obj, form, change):
        """Emails a PICKUP customer the moment staff move their order to the
        "ready" stage of the pipeline (labelled "Ready for Pickup" for these
        orders - see Order.PICKUP_STATUS_LABELS)."""
        just_became_ready = (
            change and "status" in form.changed_data
            and obj.status == Order.Status.OUT_FOR_DELIVERY
            and obj.delivery_method == Order.DeliveryMethod.PICKUP
            and not obj.pickup_ready_notified_at
        )
        super().save_model(request, obj, form, change)
        if just_became_ready:
            obj.pickup_ready_notified_at = timezone.now()
            obj.save(update_fields=["pickup_ready_notified_at"])
            send_pickup_ready_notification(obj)


@admin.register(BulkDiscountRule)
class BulkDiscountRuleAdmin(admin.ModelAdmin):
    list_display = ("minimum_order_amount", "discount_percentage", "active")


@admin.register(PaymentAccount)
class PaymentAccountAdmin(admin.ModelAdmin):
    list_display = ("bank_name", "account_name", "account_number", "active")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "valid_from", "valid_until",
                     "times_used", "max_uses", "active")
    list_filter = ("active", "discount_type")
    search_fields = ("code",)
    readonly_fields = ("times_used",)
