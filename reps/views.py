import functools
import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from reps.emails import send_employment_verification_decision
from reps.forms import EmploymentVerificationForm, GuarantorForm, InvoiceForm, InvoiceItemFormSet, RepRegisterForm
from reps.models import EmploymentVerification, Guarantor, Invoice, Receipt, SalesRep
from reps.pdf_forms import build_invoice_pdf, build_receipt_pdf
from store.models import BookPrice

logger = logging.getLogger(__name__)

# Plain @login_required redirects to settings.LOGIN_URL ("login"), which
# doesn't exist under reps.subdomain_urls - that urlconf only knows
# "reps:login". Without this, every one of these views 500s for a logged-out
# visitor instead of redirecting to the rep login page.
reps_login_required = functools.partial(login_required, login_url="reps:login")


def _get_sales_rep(request):
    return get_object_or_404(SalesRep, user=request.user)


def _school_book_prices():
    """Institution-tier book prices keyed by book id then location - lets
    the invoice form auto-fill a unit price once a rep picks a book and the
    customer's location, instead of the rep needing to know it by memory."""
    prices = {}
    for price in BookPrice.objects.filter(
        account_type=BookPrice.AccountType.SCHOOL, price__isnull=False, book__is_published=True
    ):
        prices.setdefault(str(price.book_id), {})[price.location] = str(price.price)
    return prices


def register(request):
    if request.method == "POST":
        form = RepRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            SalesRep.objects.create(user=user)
            login(request, user, backend="accounts.backends.EmailBackend")
            return redirect("reps:employment_verification")
    else:
        form = RepRegisterForm()
    return render(request, "reps/register.html", {"register_form": form})


@reps_login_required
def employment_verification(request):
    sales_rep = _get_sales_rep(request)
    existing = EmploymentVerification.objects.filter(sales_rep=sales_rep).first()
    if existing and existing.status != EmploymentVerification.Status.REJECTED:
        return redirect("reps:employment_verification_status")

    existing_guarantor = Guarantor.objects.filter(employment_verification=existing).first() if existing else None

    if request.method == "POST":
        # A rejected submission is replaced rather than edited, so the rep
        # resubmits cleanly and staff review a fresh record.
        # Prefixed so its field names ("full_name", "passport_photo", ...) don't
        # collide with the employment form's identical field names in the
        # same <form> tag.
        form = EmploymentVerificationForm(request.POST, request.FILES, instance=existing)
        guarantor_form = GuarantorForm(
            request.POST, request.FILES, instance=existing_guarantor, prefix="guarantor")
        if form.is_valid() and guarantor_form.is_valid():
            verification = form.save(commit=False)
            verification.sales_rep = sales_rep
            verification.status = EmploymentVerification.Status.PENDING
            verification.reviewed_at = None
            verification.review_notes = ""
            form.save()

            guarantor = guarantor_form.save(commit=False)
            guarantor.employment_verification = verification
            guarantor_form.save()

            messages.success(request, "Thanks - your employment and guarantor forms are with our team for review.")
            return redirect("reps:employment_verification_status")
    else:
        initial = {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "phone_number": sales_rep.phone_number,
        }
        form = EmploymentVerificationForm(instance=existing, initial=initial)
        guarantor_form = GuarantorForm(instance=existing_guarantor, prefix="guarantor")

    return render(request, "reps/employment_verification.html", {
        "verification_form": form,
        "guarantor_form": guarantor_form,
        "rejected": existing,
    })


@reps_login_required
def employment_verification_status(request):
    sales_rep = _get_sales_rep(request)
    verification = EmploymentVerification.objects.filter(sales_rep=sales_rep).first()
    if not verification:
        return redirect("reps:employment_verification")
    return render(request, "reps/employment_verification_status.html", {"verification": verification})


@reps_login_required
def employment_verification_photo(request, pk):
    """Serves the applicant's passport photo out of the database. Staff can
    see any; a rep can only see their own."""
    verification = get_object_or_404(EmploymentVerification, pk=pk)
    if not request.user.is_staff and verification.sales_rep.user_id != request.user.id:
        raise Http404
    if not verification.passport_photo:
        raise Http404
    return HttpResponse(bytes(verification.passport_photo),
                        content_type=verification.passport_photo_content_type or "image/jpeg")


@reps_login_required
def guarantor_photo(request, pk):
    """Serves the guarantor's passport photo out of the database. Staff can
    see any; a rep can only see their own guarantor's."""
    guarantor = get_object_or_404(Guarantor, pk=pk)
    if not request.user.is_staff and guarantor.employment_verification.sales_rep.user_id != request.user.id:
        raise Http404
    if not guarantor.passport_photo:
        raise Http404
    return HttpResponse(bytes(guarantor.passport_photo),
                        content_type=guarantor.passport_photo_content_type or "image/jpeg")


@reps_login_required
def dashboard(request):
    sales_rep = _get_sales_rep(request)
    if not sales_rep.is_approved:
        return redirect("reps:employment_verification_status")
    invoices = sales_rep.invoices.order_by("-created_at")
    return render(request, "reps/dashboard.html", {"invoices": invoices, "sales_rep": sales_rep})


@reps_login_required
def invoice_create(request):
    sales_rep = _get_sales_rep(request)
    if not sales_rep.is_approved:
        messages.error(request, "You can't log invoices until your employment form is approved.")
        return redirect("reps:employment_verification_status")

    if request.method == "POST":
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST, instance=Invoice())
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.sales_rep = sales_rep
            invoice.save()
            formset.instance = invoice
            formset.save()
            messages.success(request, f"Invoice {invoice.invoice_number} created.")
            return redirect("reps:invoice_detail", pk=invoice.pk)
    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet(instance=Invoice())

    return render(request, "reps/invoice_form.html", {
        "form": form, "formset": formset, "book_prices": _school_book_prices(),
    })


@reps_login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if not request.user.is_staff:
        sales_rep = _get_sales_rep(request)
        if invoice.sales_rep_id != sales_rep.id:
            raise Http404
    return render(request, "reps/invoice_detail.html", {"invoice": invoice})


@reps_login_required
@require_POST
def invoice_mark_paid(request, pk):
    sales_rep = _get_sales_rep(request)
    invoice = get_object_or_404(Invoice, pk=pk, sales_rep=sales_rep)
    if invoice.status == Invoice.Status.PENDING_PAYMENT:
        invoice.status = Invoice.Status.PAID
        invoice.paid_at = timezone.now()
        invoice.save(update_fields=["status", "paid_at"])
        Receipt.objects.get_or_create(invoice=invoice)
        messages.success(request, f"Payment confirmed - the receipt for {invoice.invoice_number} is ready to download.")
    return redirect("reps:invoice_detail", pk=invoice.pk)


@reps_login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if not request.user.is_staff:
        sales_rep = _get_sales_rep(request)
        if invoice.sales_rep_id != sales_rep.id:
            raise Http404
    content = build_invoice_pdf(invoice)
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{invoice.invoice_number}.pdf"'
    return response


@reps_login_required
def receipt_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if not request.user.is_staff:
        sales_rep = _get_sales_rep(request)
        if invoice.sales_rep_id != sales_rep.id:
            raise Http404
    if not hasattr(invoice, "receipt"):
        raise Http404
    content = build_receipt_pdf(invoice)
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{invoice.receipt.receipt_number}.pdf"'
    return response


class PasswordResetView(BasePasswordResetView):
    """An SMTP outage shouldn't crash the page with a raw 500 - mirrors
    accounts.views.PasswordResetView."""

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception:
            logger.exception("Failed to send rep password reset email")
            return redirect(self.get_success_url())
