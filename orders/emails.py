import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string

from orders.models import PaymentAccount

logger = logging.getLogger(__name__)


def send_order_confirmation(order):
    """Best-effort - an email outage must never break checkout, so any
    failure here is logged and swallowed rather than raised."""
    try:
        payment_accounts = PaymentAccount.objects.filter(active=True)
        body = render_to_string("orders/order_confirmation_email.txt", {
            "order": order,
            "payment_accounts": payment_accounts,
        })
        send_mail(
            subject=f"LearnRite Order {order.order_reference} received",
            message=body,
            from_email=None,
            recipient_list=[order.email],
        )
    except Exception:
        logger.exception("Failed to send order confirmation email for %s", order.order_reference)
