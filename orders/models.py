import secrets
from decimal import Decimal

from django.contrib import auth
from django.db import models
from django.utils import timezone

from accounts.models import Address
from store.models import Book


class Cart(models.Model):
    """One cart per account. Individuals never get self-service pricing or
    checkout (see accounts.templatetags.accounts_extras) and institutions
    must always be logged in, so there is no scenario needing a guest/
    session-keyed cart - every cart belongs to exactly one user."""
    user = models.OneToOneField \
        (auth.get_user_model(), on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart({self.user.username})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "book")

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"


class BulkDiscountRule(models.Model):
    """Orders at or above minimum_order_amount get discount_percentage off
    automatically, no code entry - separate from a future Coupon system.
    Admin-editable rather than hardcoded since the client asked for this
    threshold/rate to be tweakable without a deploy."""
    minimum_order_amount = models.DecimalField(max_digits=12, decimal_places=2, default=500000)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.discount_percentage}% off orders >= {self.minimum_order_amount}"


class PaymentAccount(models.Model):
    """A bank account shown to customers on their order confirmation so
    they can pay by transfer - admin-editable so account details can
    change without a deploy. Usually just one row."""
    bank_name = models.CharField(max_length=100)
    account_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=20)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class Coupon(models.Model):
    """A discount code entered by the customer at checkout - separate from
    BulkDiscountRule above, which applies automatically with no code. Both
    can apply to the same order (stacking, matching the client's own
    "5% and above" discount table on their printed price lists, which
    already stacks with whatever else a school negotiates)."""
    class DiscountType(models.TextChoices):
        PERCENTAGE = "PERCENTAGE", "Percentage"
        FIXED = "FIXED", "Fixed Amount"

    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(choices=DiscountType.choices, max_length=20)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="Leave blank for unlimited uses.")
    times_used = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.active:
            return False
        if not (self.valid_from <= now <= self.valid_until):
            return False
        if self.max_uses is not None and self.times_used >= self.max_uses:
            return False
        return True

    def calculate_discount(self, subtotal):
        if self.discount_type == self.DiscountType.PERCENTAGE:
            return (subtotal * self.discount_value / Decimal("100")).quantize(Decimal("0.01"))
        return min(self.discount_value, subtotal)


def _generate_order_reference():
    return "LR-" + secrets.token_hex(4).upper()


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Payment"
        PAID = "PAID", "Paid"
        FULFILLED = "FULFILLED", "Fulfilled"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey \
        (auth.get_user_model(), null=True, on_delete=models.SET_NULL, related_name="orders")
    order_reference = models.CharField(max_length=20, unique=True, default=_generate_order_reference)
    email = models.EmailField()
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    shipping_address = models.ForeignKey \
        (Address, null=True, on_delete=models.SET_NULL, related_name="orders")
    status = models.CharField(choices=Status.choices, max_length=20, default=Status.PENDING)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField \
        (max_digits=12, decimal_places=2, default=0, help_text="Automatic bulk-order discount only.")
    coupon = models.ForeignKey \
        (Coupon, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    coupon_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_reference} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    title = models.CharField(max_length=70)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.title}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
