from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from store.forms import ReviewForm, SearchForm
from store.models import Book, Review
from accounts.forms import AccountSetupForm, ProfileForm, RegisterForm
from accounts.models import WishlistItem

from orders.models import Order, OrderItem


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
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("index")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {
        "register_form": form,
        "form": SearchForm(request.GET),
    })


@login_required
def confirm_account_setup(request):
    profile = request.user.profile
    if profile.profile_confirmed:
        return redirect("index")
    if request.method == "POST":
        setup_form = AccountSetupForm(request.POST, instance=profile)
        if setup_form.is_valid():
            setup_form.save()
            return redirect("index")
    else:
        setup_form = AccountSetupForm(instance=profile)
    return render(request, "accounts/confirm_account_setup.html", {
        "setup_form": setup_form,
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
        order__status__in=[Order.Status.PAID, Order.Status.FULFILLED],
    ).values_list("book_id", flat=True).distinct()
    existing_reviews = {
        review.book_id: review
        for review in Review.objects.filter(creator=request.user, book_id__in=purchased_book_ids)
    }
    reviewable_books = [
        {"book": book, "review": existing_reviews.get(book.pk), "review_form": ReviewForm(instance=existing_reviews.get(book.pk))}
        for book in Book.objects.filter(pk__in=purchased_book_ids)
    ]

    return render(request, "accounts/profile.html", {
        "profile_form": profile_form,
        "reviewable_books": reviewable_books,
        "form": SearchForm(request.GET),
    })


@login_required
@require_POST
def wishlist_toggle(request, pk):
    book = get_object_or_404(Book, pk=pk)
    item, created = WishlistItem.objects.get_or_create(user=request.user, book=book)
    if not created:
        item.delete()
        messages.success(request, f'Removed "{book.title}" from your wishlist.')
    else:
        messages.success(request, f'Added "{book.title}" to your wishlist.')
    return _redirect_back(request, "books")


@login_required
def wishlist_view(request):
    items = WishlistItem.objects.filter(user=request.user).select_related("book").prefetch_related(
        "book__contributors", "book__prices", "book__review_set"
    )
    books = [item.book for item in items]
    return render(request, "accounts/wishlist.html", {
        "books": books,
        "form": SearchForm(request.GET),
    })
