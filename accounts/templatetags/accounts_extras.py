from django import template

from store.models import BookPrice
from store.utils import get_book_price

register = template.Library()

CONTACT_MESSAGE = "Contact us at learninsideout@yahoo.com for pricing."
LOGIN_PROMPT_MESSAGE = "Log in or sign up to see pricing."
PRICING_PENDING_MESSAGE = "Pricing for your account isn't set up yet - contact us to order."


@register.simple_tag
def book_purchase_context(book, user):
    """Individuals never get self-service pricing/checkout, regardless of
    order size - they always see a contact-us message. Institutions get a
    real per-unit price from BookPrice (same one used everywhere else),
    or a distinct "pricing coming soon" message if that tier is unpriced.

    A visitor who isn't logged in at all is a different case from a known
    individual account: they might be an unregistered school, so nudge them
    to log in/register instead of assuming they can never buy."""
    if not user.is_authenticated:
        return {"can_buy": False, "price": None, "message": LOGIN_PROMPT_MESSAGE, "variant": "login"}

    if user.profile.account_type != BookPrice.AccountType.SCHOOL:
        return {"can_buy": False, "price": None, "message": CONTACT_MESSAGE, "variant": "contact"}

    price = get_book_price(book, user.profile)
    if price is None:
        return {"can_buy": False, "price": None, "message": PRICING_PENDING_MESSAGE, "variant": "pending"}

    return {"can_buy": True, "price": price, "message": None, "variant": None}
