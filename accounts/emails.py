import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.tokens import email_verification_token

logger = logging.getLogger(__name__)


def send_verification_email(request, user):
    """Best-effort - an email outage must never break registration."""
    try:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = email_verification_token.make_token(user)
        link = request.build_absolute_uri(reverse("verify_email", kwargs={"uidb64": uid, "token": token}))
        body = render_to_string("accounts/verification_email.txt", {"user": user, "link": link})
        send_mail(
            subject="Verify your LearnRite account",
            message=body,
            from_email=None,
            recipient_list=[user.email],
        )
    except Exception:
        logger.exception("Failed to send verification email to %s", user.email)
