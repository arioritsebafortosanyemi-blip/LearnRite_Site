from django import template

from store.models import BookPrice
from store.utils import get_book_price

register = template.Library()

CONTACT_MESSAGE = "Contact us at learninsideout@yahoo.com for pricing."
PRICING_PENDING_MESSAGE = "Pricing for your account isn't set up yet - contact us to order."


@register.simple_tag
def book_purchase_context(book, user):
    """Individuals never get self-service pricing/checkout, regardless of
    order size - they always see a contact-us message. Institutions get a
    real per-unit price from BookPrice (same one used everywhere else),
    or a distinct "pricing coming soon" message if that tier is unpriced."""
    if not user.is_authenticated or user.profile.account_type != BookPrice.AccountType.SCHOOL:
        return {"can_buy": False, "price": None, "message": CONTACT_MESSAGE, "variant": "contact"}

    price = get_book_price(book, user.profile)
    if price is None:
        return {"can_buy": False, "price": None, "message": PRICING_PENDING_MESSAGE, "variant": "pending"}

    return {"can_buy": True, "price": price, "message": None, "variant": None}
