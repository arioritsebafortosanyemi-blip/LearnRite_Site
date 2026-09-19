import logging

from django.core.mail import EmailMessage, send_mail
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


def send_invoice_to_school(invoice):
    """Emails the school its own copy of the invoice, triggered by staff
    from admin (see reps.admin.InvoiceAdmin.send_to_school) once a sales
    rep has entered the sale - the client-facing PDF (no commission line),
    never the internal one."""
    from reps.pdf_forms import build_invoice_pdf

    try:
        body = (
            f"Dear {invoice.customer_name},\n\n"
            f"Please find attached your invoice {invoice.invoice_number} from LearnRite International "
            f"Publishers.\n\nIf you have any questions, contact us at learninsideout@yahoo.com or "
            f"+234-907-776-5490.\n\n- LearnRite International Publishers"
        )
        message = EmailMessage(
            subject=f"Your LearnRite invoice {invoice.invoice_number}",
            body=body,
            from_email=None,
            to=[invoice.customer_email],
        )
        message.attach(f"{invoice.invoice_number}.pdf", build_invoice_pdf(invoice), "application/pdf")
        message.send()
    except Exception:
        logger.exception("Failed to send invoice %s to %s", invoice.invoice_number, invoice.customer_email)
