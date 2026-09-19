import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from store.forms import ReviewForm, SearchForm
from store.models import Book, BookPrice, Review

from accounts.pdf_forms import build_consent_pdf, build_mandate_pdf
from accounts.emails import send_verification_email
from accounts.forms import (AccountSetupForm, AddressSetupForm, ProfileForm, RegisterForm,
                            SchoolVerificationForm)
from accounts.models import Profile, SchoolVerification, WishlistItem
from accounts.tokens import email_verification_token

from orders.models import Order, OrderItem

logger = logging.getLogger(__name__)


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _redirect_back(request, fallback):
    """Return to the page a toggle was submitted from rather than always
    bouncing to a fixed page - but only to a same-site URL, since
    HTTP_REFERER is client-supplied."""
    referer = request.META.get("HTTP_REFERER")
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}):
        return redirect(referer)
    return redirect(fallback)


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(request, user)
            login(request, user, backend="accounts.backends.EmailBackend")
            return redirect("index")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {
        "register_form": form,
        "form": SearchForm(request.GET),
    })


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.save(update_fields=["email_verified"])
        messages.success(request, "Your email has been verified.")
    else:
        messages.error(request, "That verification link is invalid or has expired.")

    if request.user.is_authenticated:
        return redirect("account_setup")
    return redirect("login")


@login_required
@require_POST
def resend_verification_email(request):
    if not request.user.profile.is_verified:
        send_verification_email(request, request.user)
        messages.success(request, f"We've sent a new verification link to {request.user.email}.")
    return redirect("verify_email_pending")


@login_required
def verify_email_pending(request):
    if request.user.profile.is_verified:
        return redirect("account_setup" if not request.user.profile.profile_confirmed else "index")
    return render(request, "accounts/verify_email_pending.html", {
        "form": SearchForm(request.GET),
    })


@login_required
def confirm_account_setup(request):
    profile = request.user.profile
    if profile.profile_confirmed:
        return redirect("index")
    if not profile.is_verified:
        return redirect("verify_email_pending")

    default_address = request.user.addresses.filter(is_default=True).first()
    if request.method == "POST":
        setup_form = AccountSetupForm(request.POST, instance=profile)
        address_form = AddressSetupForm(request.POST, instance=default_address)
        if setup_form.is_valid() and address_form.is_valid():
            setup_form.save()
            address = address_form.save(commit=False)
            address.user = request.user
            address.full_name = request.user.first_name or request.user.username
            address.phone_number = setup_form.cleaned_data["phone_number"]
            address.is_default = True
            address.save()
            # A school account can't order until its mandate/consent forms
            # are approved (see orders.views._school_purchase_block) and had
            # no way to find that form otherwise - nothing in the nav links
            # to it, so send them there directly instead of the homepage.
            if profile.account_type == BookPrice.AccountType.SCHOOL:
                return redirect("school_verification")
            return redirect("index")
    else:
        setup_form = AccountSetupForm(instance=profile)
        address_form = AddressSetupForm(instance=default_address)
    return render(request, "accounts/confirm_account_setup.html", {
        "setup_form": setup_form,
        "address_form": address_form,
        "form": SearchForm(request.GET),
    })


@login_required
def profile(request):
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            return redirect("profile")
    else:
        profile_form = ProfileForm(instance=request.user.profile)

    purchased_book_ids = OrderItem.objects.filter(
        order__user=request.user,
        order__status__in=Order.PIPELINE_STATUSES,
    ).values_list("book_id", flat=True).distinct()
    existing_reviews = {
        review.book_id: review
        for review in Review.objects.filter(creator=request.user, book_id__in=purchased_book_ids)
    }
    reviewable_books = [
        {"book": book, "review": existing_reviews.get(book.pk), "review_form": ReviewForm(instance=existing_reviews.get(book.pk))}
        for book in Book.objects.filter(pk__in=purchased_book_ids)
    ]

    school_verification = None
    if request.user.profile.account_type == BookPrice.AccountType.SCHOOL:
        school_verification = SchoolVerification.objects.filter(profile=request.user.profile).first()

    return render(request, "accounts/profile.html", {
        "profile_form": profile_form,
        "reviewable_books": reviewable_books,
        "school_verification": school_verification,
        "form": SearchForm(request.GET),
    })


@login_required
def school_verification(request):
    """The mandate + consent forms. Institution accounts only - an individual
    account has no school to verify, and never gets self-service checkout
    anyway."""
    profile = request.user.profile
    if profile.account_type != BookPrice.AccountType.SCHOOL:
        messages.error(request, "Only institution accounts need to complete these forms.")
        return redirect("profile")

    existing = SchoolVerification.objects.filter(profile=profile).first()
    if existing and existing.status != SchoolVerification.Status.REJECTED:
        return redirect("school_verification_status")

    if request.method == "POST":
        # A rejected submission is replaced rather than edited, so the school
        # resubmits cleanly and staff review a fresh record.
        form = SchoolVerificationForm(request.POST, request.FILES, instance=existing)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.profile = profile
            verification.status = SchoolVerification.Status.PENDING
            verification.reviewed_at = None
            verification.review_notes = ""
            form.save()
            messages.success(request, "Thanks - your forms are with our team for review.")
            return redirect("school_verification_status")
    else:
        initial = {
            "school_name": profile.organization_name,
            "staff_name": request.user.first_name,
            "owner_phone": profile.phone_number,
        }
        form = SchoolVerificationForm(instance=existing, initial=initial)

    return render(request, "accounts/school_verification.html", {
        "verification_form": form,
        "rejected": existing,
        "form": SearchForm(request.GET),
    })


@login_required
def school_verification_status(request):
    verification = SchoolVerification.objects.filter(profile=request.user.profile).first()
    if not verification:
        return redirect("school_verification")
    return render(request, "accounts/school_verification_status.html", {
        "verification": verification,
        "form": SearchForm(request.GET),
    })


@login_required
def school_verification_photo(request, pk):
    """Serves the passport photo out of the database. Staff can see any;
    a customer can only see their own."""
    verification = get_object_or_404(SchoolVerification, pk=pk)
    if not request.user.is_staff and verification.profile.user_id != request.user.id:
        raise Http404
    if not verification.passport_photo:
        raise Http404
    return HttpResponse(bytes(verification.passport_photo),
                        content_type=verification.passport_photo_content_type or "image/jpeg")


@staff_member_required
def school_verification_pdf(request, pk, which):
    verification = get_object_or_404(SchoolVerification, pk=pk)
    if which == "mandate":
        content = build_mandate_pdf(verification)
    elif which == "consent":
        content = build_consent_pdf(verification)
    else:
        raise Http404
    response = HttpResponse(content, content_type="application/pdf")
    slug = slugify(verification.school_name) or "school"
    response["Content-Disposition"] = f'inline; filename="{which}-{slug}.pdf"'
    return response


@login_required
@require_POST
def wishlist_toggle(request, pk):
    book = get_object_or_404(Book, pk=pk)
    item, created = WishlistItem.objects.get_or_create(user=request.user, book=book)
    if not created:
        item.delete()
        wishlisted = False
        message = f'Removed "{book.title}" from your wishlist.'
    else:
        wishlisted = True
        message = f'Added "{book.title}" to your wishlist.'

    if _is_ajax(request):
        return JsonResponse({"success": True, "wishlisted": wishlisted, "message": message})
    messages.success(request, message)
    return _redirect_back(request, "books")


@login_required
def wishlist_view(request):
    items = WishlistItem.objects.filter(user=request.user, book__is_published=True).select_related("book").prefetch_related(
        "book__contributors", "book__prices", "book__review_set"
    )
    books = [item.book for item in items]
    return render(request, "accounts/wishlist.html", {
        "books": books,
        "form": SearchForm(request.GET),
    })


class PasswordResetView(BasePasswordResetView):
    """An SMTP outage shouldn't crash the page with a raw 500 - every other
    email send in this codebase fails gracefully, so this should too. The
    customer still lands on the same "check your email" page either way,
    which avoids revealing whether that email address has an account."""

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception:
            logger.exception("Failed to send password reset email")
            return redirect(self.get_success_url())
