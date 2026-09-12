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


def send_school_verification_decision(verification):
    """Tells a school its mandate/consent forms were approved or rejected.
    Best-effort like every other send here - a mail outage must never break
    a staff member's approval in admin."""
    recipient = verification.profile.user.email
    approved = verification.is_approved
    try:
        template = ("accounts/school_verification_approved_email.txt" if approved
                    else "accounts/school_verification_rejected_email.txt")
        body = render_to_string(template, {"verification": verification})
        subject = (f"{verification.school_name} is approved to order from LearnRite" if approved
                   else f"We need a few corrections for {verification.school_name}")
        send_mail(subject=subject, message=body, from_email=None, recipient_list=[recipient])
    except Exception:
        logger.exception("Failed to send school verification decision to %s", recipient)
