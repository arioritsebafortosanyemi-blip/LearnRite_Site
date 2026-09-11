from django.contrib import admin

from orders.models import BulkDiscountRule, Cart, CartItem, Order, OrderItem, PaymentAccount


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
    list_display = ("order_reference", "full_name", "email", "status", "total", "created_at")
    list_filter = ("status",)
    search_fields = ("order_reference", "full_name", "email", "phone_number")
    readonly_fields = ("order_reference", "user", "email", "full_name", "phone_number",
                       "shipping_address", "subtotal", "discount_amount", "total", "created_at")
    inlines = [OrderItemInline]


@admin.register(BulkDiscountRule)
class BulkDiscountRuleAdmin(admin.ModelAdmin):
    list_display = ("minimum_order_amount", "discount_percentage", "active")


@admin.register(PaymentAccount)
class PaymentAccountAdmin(admin.ModelAdmin):
    list_display = ("bank_name", "account_name", "account_number", "active")
