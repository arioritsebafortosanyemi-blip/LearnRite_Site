from decimal import Decimal

from store.utils import get_book_price

from orders.models import Cart


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def price_cart(cart, profile):
    """Live-priced cart lines plus the subtotal. Never trusts a cached
    price - always looks up the current BookPrice for this profile, since
    admin-set prices and the customer's own tier can both change."""
    items = cart.items.select_related("book").prefetch_related("book__prices")
    lines = []
    subtotal = Decimal("0")
    for item in items:
        price = get_book_price(item.book, profile)
        line_total = price * item.quantity if price is not None else None
        if line_total is not None:
            subtotal += line_total
        lines.append({"item": item, "price": price, "line_total": line_total})
    return lines, subtotal
