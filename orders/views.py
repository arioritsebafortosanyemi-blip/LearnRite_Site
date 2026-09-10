from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from store.forms import SearchForm
from store.models import Book, BookPrice
from store.utils import get_book_price

from orders.models import CartItem
from orders.utils import get_or_create_cart


def _redirect_back(request, fallback):
    """Return to the page Add to Cart / update was submitted from, e.g. a
    book grid, rather than always bouncing to a fixed page - but only to a
    same-site URL, since HTTP_REFERER is client-supplied."""
    referer = request.META.get("HTTP_REFERER")
    if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}):
        return redirect(referer)
    return redirect(fallback)


def _clean_quantity(raw, default=1):
    try:
        quantity = int(raw)
    except (TypeError, ValueError):
        return default
    return quantity if quantity > 0 else default


@login_required
@require_POST
def add_to_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    profile = request.user.profile

    if profile.account_type != BookPrice.AccountType.SCHOOL:
        messages.error(request, "Only institution accounts can order online - individuals should contact us.")
        return _redirect_back(request, "books")

    if get_book_price(book, profile) is None:
        messages.error(request, f'Pricing for "{book.title}" isn\'t set up for your account yet - contact us to order.')
        return _redirect_back(request, "books")

    quantity = _clean_quantity(request.POST.get("quantity"))
    cart = get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, book=book, defaults={"quantity": quantity})
    if not created:
        item.quantity += quantity
        item.save()

    messages.success(request, f'Added "{book.title}" to your cart.')
    return _redirect_back(request, "books")


@login_required
def cart_detail(request):
    cart = get_or_create_cart(request.user)
    profile = request.user.profile
    items = cart.items.select_related("book").prefetch_related("book__prices")

    lines = []
    subtotal = Decimal("0")
    for item in items:
        price = get_book_price(item.book, profile)
        line_total = price * item.quantity if price is not None else None
        if line_total is not None:
            subtotal += line_total
        lines.append({"item": item, "price": price, "line_total": line_total})

    return render(request, "orders/cart_detail.html", {
        "lines": lines,
        "subtotal": subtotal,
        "form": SearchForm(request.GET),
    })


@login_required
@require_POST
def update_cart_item(request, pk):
    cart = get_or_create_cart(request.user)
    item = get_object_or_404(CartItem, pk=pk, cart=cart)
    quantity = _clean_quantity(request.POST.get("quantity"), default=0)
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save()
    return redirect("cart_detail")


@login_required
@require_POST
def remove_cart_item(request, pk):
    cart = get_or_create_cart(request.user)
    get_object_or_404(CartItem, pk=pk, cart=cart).delete()
    return redirect("cart_detail")
