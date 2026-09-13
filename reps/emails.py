import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_employment_verification_decision(verification):
    """Tells a sales rep their employment and indemnity form was approved or
    rejected. Best-effort like every other send in this codebase - a mail
    outage must never break a staff member's approval in admin."""
    recipient = verification.sales_rep.user.email
    approved = verification.is_approved
    try:
        template = ("reps/employment_verification_approved_email.txt" if approved
                    else "reps/employment_verification_rejected_email.txt")
        body = render_to_string(template, {"verification": verification})
        subject = ("You're approved to start issuing invoices for LearnRite" if approved
                   else "We need a few corrections to your employment form")
        send_mail(subject=subject, message=body, from_email=None, recipient_list=[recipient])
    except Exception:
        logger.exception("Failed to send employment verification decision to %s", recipient)
