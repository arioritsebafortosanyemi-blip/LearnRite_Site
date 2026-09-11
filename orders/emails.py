import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string

from orders.models import PaymentAccount

logger = logging.getLogger(__name__)

STAFF_NOTIFICATION_EMAIL = "learninsideout@yahoo.com"


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


def send_pickup_ready_notification(order):
    """Tells a store-pickup customer their order is ready to collect -
    triggered when staff move a PICKUP order's status to the "ready" stage
    in admin (see orders.admin.OrderAdmin.save_model)."""
    try:
        body = render_to_string("orders/pickup_ready_email.txt", {"order": order})
        send_mail(
            subject=f"Your LearnRite order {order.order_reference} is ready for pickup",
            message=body,
            from_email=None,
            recipient_list=[order.email],
        )
    except Exception:
        logger.exception("Failed to send pickup-ready email for %s", order.order_reference)


def send_payment_claimed_notification(order):
    """Notifies staff that a customer says they've paid - a claim to go
    verify, not confirmation the payment actually landed."""
    try:
        body = (
            f"{order.full_name} ({order.email}) says they've completed payment for "
            f"order {order.order_reference} (total N{order.total}).\n\n"
            f"Please verify the bank transfer and update the order status in admin:\n"
            f"https://learnritepublishers.com/admin/orders/order/{order.pk}/change/"
        )
        send_mail(
            subject=f"Payment claimed for order {order.order_reference}",
            message=body,
            from_email=None,
            recipient_list=[STAFF_NOTIFICATION_EMAIL],
        )
    except Exception:
        logger.exception("Failed to send payment-claimed notification for %s", order.order_reference)
