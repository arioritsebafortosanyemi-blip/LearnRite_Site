from django.contrib import admin, messages
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

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
    list_display = ("order_reference", "full_name", "email", "status", "amount_paid", "amount_claimed",
                     "balance_due_display", "total", "created_at")
    list_filter = ("status", ("amount_claimed", admin.EmptyFieldListFilter))
    search_fields = ("order_reference", "full_name", "email", "phone_number")
    readonly_fields = ("order_reference", "user", "email", "full_name", "phone_number", "delivery_method",
                       "shipping_address", "subtotal", "discount_amount", "coupon",
                       "coupon_discount_amount", "total", "amount_paid", "amount_claimed",
                       "balance_due_display", "invoice_link", "created_at")
    inlines = [OrderItemInline]
    actions = ("approve_payment_claim",)

    @admin.display(description="Balance Due")
    def balance_due_display(self, obj):
        return obj.balance_due

    @admin.display(description="Invoice")
    def invoice_link(self, obj):
        if not obj.pk:
            return "-"
        style = ("display:inline-block;padding:6px 14px;border-radius:6px;"
                 "background:#fe5d26;color:#fff;font-weight:600;text-decoration:none;")
        url = reverse("order_invoice_pdf", args=[obj.pk])
        return format_html('<a style="{}" href="{}" target="_blank">Invoice (PDF)</a>', style, url)

    @staticmethod
    def _fold_in_claim(order):
        """Adds a pending amount_claimed into amount_paid and sets the
        correct payment status for the resulting balance. Shared by the
        bulk action and save_model below, so a claim gets reconciled
        whichever way staff confirm it - moving status by hand on the
        change form used to leave amount_paid at 0 even though the status
        said otherwise, since nothing tied the two together outside the
        dedicated action."""
        if order.amount_claimed is None:
            return
        order.amount_paid += order.amount_claimed
        order.amount_claimed = None
        order.status = (
            Order.Status.FULL_PAYMENT_RECEIVED if order.amount_paid >= order.total
            else Order.Status.PART_PAYMENT_RECEIVED
        )

    @admin.action(description="Approve payment claim (adds to amount paid, updates status)")
    def approve_payment_claim(self, request, queryset):
        count = 0
        for order in queryset.filter(amount_claimed__isnull=False):
            self._fold_in_claim(order)
            order.save(update_fields=["amount_paid", "amount_claimed", "status"])
            count += 1
        self.message_user(request, f"{count} payment claim(s) approved.", messages.SUCCESS)

    def save_model(self, request, obj, form, change):
        """status is the only field staff can actually edit here, so any
        save is a deliberate status update - folds in a pending claim right
        then rather than requiring the separate "Approve payment claim"
        action, and also emails a customer the moment their order moves to
        the "ready" stage of the pipeline."""
        self._fold_in_claim(obj)
        just_became_ready = (
            change and "status" in form.changed_data
            and obj.status == Order.Status.READY_FOR_PICKUP
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
