from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from store.forms import SearchForm
from store.models import Book, BookPrice
from store.utils import get_book_price

from orders.emails import send_order_confirmation, send_payment_claimed_notification
from orders.forms import CheckoutForm
from orders.models import BulkDiscountRule, CartItem, Coupon, Order, OrderItem, PaymentAccount
from orders.pdf_forms import build_order_invoice_pdf
from orders.utils import get_or_create_cart, price_cart


def _is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


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


def _cart_count(user):
    return CartItem.objects.filter(cart__user=user, book__is_published=True).aggregate(total=Sum("quantity"))["total"] or 0


def _school_purchase_block(profile):
    """(message, verification_redirect) if this profile can't buy online
    yet, else None. verification_redirect is the named URL for the specific
    reason - None for the plain individual-account case, since callers
    already have their own place to send those back to."""
    if profile.account_type != BookPrice.AccountType.SCHOOL:
        return "Only institution accounts can order online - individuals should contact us.", None

    # The client requires a signed mandate and stamping consent from every
    # school before it can order, so buying waits on staff approval.
    verification = getattr(profile, "school_verification", None)
    if verification is None:
        return "Please complete your school's mandate and consent forms before ordering.", "school_verification"
    if not verification.is_approved:
        return "Your school's forms are still being reviewed - we'll email you once they're approved.", "school_verification_status"
    return None


@login_required
@require_POST
def add_to_cart(request, pk):
    book = get_object_or_404(Book, pk=pk)
    profile = request.user.profile

    block = _school_purchase_block(profile)
    if block:
        message, verification_redirect = block
        if _is_ajax(request):
            return JsonResponse({"success": False, "message": message}, status=400)
        messages.error(request, message)
        return redirect(verification_redirect) if verification_redirect else _redirect_back(request, "books")

    if get_book_price(book, profile) is None:
        message = f'Pricing for "{book.title}" isn\'t set up for your account yet - contact us to order.'
        if _is_ajax(request):
            return JsonResponse({"success": False, "message": message}, status=400)
        messages.error(request, message)
        return _redirect_back(request, "books")

    quantity = _clean_quantity(request.POST.get("quantity"))
    cart = get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, book=book, defaults={"quantity": quantity})
    if not created:
        item.quantity += quantity
        item.save()

    message = f'Added "{book.title}" to your cart.'
    if _is_ajax(request):
        return JsonResponse({"success": True, "message": message, "cart_count": _cart_count(request.user)})
    messages.success(request, message)
    return _redirect_back(request, "books")


@login_required
def cart_detail(request):
    cart = get_or_create_cart(request.user)
    lines, subtotal = price_cart(cart, request.user.profile)

    return render(request, "orders/cart_detail.html", {
        "lines": lines,
        "subtotal": subtotal,
        "unavailable_lines": any(line["price"] is None for line in lines),
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


def _apply_bulk_discount(subtotal):
    """Automatic discount for large orders - separate from the Coupon
    system below, applied whenever subtotal clears the threshold."""
    rule = BulkDiscountRule.objects.filter(active=True).first()
    if rule and subtotal >= rule.minimum_order_amount:
        return (subtotal * rule.discount_percentage / Decimal("100")).quantize(Decimal("0.01"))
    return Decimal("0")


def _resolve_coupon(code):
    """(coupon, error_message) for a submitted code - never trust a code
    just because it was accepted earlier; re-checked on every submission
    since a coupon can expire or hit max_uses between page loads."""
    code = (code or "").strip()
    if not code:
        return None, None
    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return None, "That coupon code isn't valid."
    if not coupon.is_valid():
        return None, "That coupon code has expired or is no longer available."
    return coupon, None


@login_required
def checkout(request):
    profile = request.user.profile
    cart = get_or_create_cart(request.user)

    block = _school_purchase_block(profile)
    if block:
        message, verification_redirect = block
        messages.error(request, message)
        return redirect(verification_redirect or "cart_detail")

    lines, subtotal = price_cart(cart, profile)
    if not lines:
        messages.error(request, "Your cart is empty.")
        return redirect("cart_detail")
    if any(line["price"] is None for line in lines):
        messages.error(request, "Some items in your cart don't have pricing set up yet - remove them or contact us to order.")
        return redirect("cart_detail")

    discount_amount = _apply_bulk_discount(subtotal)
    coupon_discount_amount = Decimal("0")

    if request.method == "POST":
        checkout_form = CheckoutForm(request.POST)
        form_valid = checkout_form.is_valid()
        coupon, coupon_error = _resolve_coupon(checkout_form.data.get("coupon_code"))
        if coupon_error:
            checkout_form.add_error("coupon_code", coupon_error)

        if form_valid and not coupon_error:
            # Re-price at submission time rather than trusting the GET-time
            # figures above, in case prices or the cart changed in between.
            lines, subtotal = price_cart(cart, profile)
            if not lines or any(line["price"] is None for line in lines):
                messages.error(request, "Your cart changed - please review it and try again.")
                return redirect("cart_detail")
            discount_amount = _apply_bulk_discount(subtotal)
            coupon_discount_amount = coupon.calculate_discount(subtotal) if coupon else Decimal("0")
            total = max(subtotal - discount_amount - coupon_discount_amount, Decimal("0"))

            order = Order.objects.create(
                user=request.user,
                email=request.user.email,
                full_name=checkout_form.cleaned_data["full_name"],
                phone_number=checkout_form.cleaned_data["phone_number"],
                subtotal=subtotal,
                discount_amount=discount_amount,
                coupon=coupon,
                coupon_discount_amount=coupon_discount_amount,
                total=total,
            )
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    book=line["item"].book,
                    title=line["item"].book.title,
                    unit_price=line["price"],
                    quantity=line["item"].quantity,
                )
                for line in lines
            ])
            cart.items.all().delete()

            if coupon:
                coupon.times_used += 1
                coupon.save(update_fields=["times_used"])

            send_order_confirmation(order)

            return redirect("order_detail", pk=order.pk)
    else:
        checkout_form = CheckoutForm(initial={
            "full_name": request.user.get_full_name() or request.user.username,
            "phone_number": profile.phone_number,
        })

    total = max(subtotal - discount_amount - coupon_discount_amount, Decimal("0"))
    return render(request, "orders/checkout.html", {
        "checkout_form": checkout_form,
        "lines": lines,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "coupon_discount_amount": coupon_discount_amount,
        "total": total,
        "form": SearchForm(request.GET),
    })


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    payment_accounts = PaymentAccount.objects.filter(active=True)
    return render(request, "orders/order_detail.html", {
        "order": order,
        "payment_accounts": payment_accounts,
        "pipeline_statuses": order.pipeline_status_choices(),
        "pipeline_index": order.pipeline_index,
        "form": SearchForm(request.GET),
    })


@login_required
def order_invoice_pdf(request, pk):
    if request.user.is_staff:
        order = get_object_or_404(Order, pk=pk)
    else:
        order = get_object_or_404(Order, pk=pk, user=request.user)
    content = build_order_invoice_pdf(order)
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{order.order_reference}.pdf"'
    return response


@login_required
def order_history(request):
    orders = request.user.orders.order_by("-created_at")
    return render(request, "orders/order_history.html", {
        "orders": orders,
        "form": SearchForm(request.GET),
    })


@login_required
@require_POST
def claim_payment(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)

    # Nothing to claim: already cancelled, already fully paid, or a previous
    # claim is still awaiting staff approval (see OrderAdmin.approve_payment_claim).
    if order.status == Order.Status.CANCELLED or order.balance_due <= 0 or order.amount_claimed is not None:
        return redirect("order_detail", pk=order.pk)

    if request.POST.get("payment_type") == "part":
        try:
            amount = Decimal((request.POST.get("amount") or "").strip())
        except InvalidOperation:
            messages.error(request, "Enter a valid amount.")
            return redirect("order_detail", pk=order.pk)
        if amount <= 0 or amount > order.balance_due:
            messages.error(request, f"Enter an amount up to your balance of N{order.balance_due}.")
            return redirect("order_detail", pk=order.pk)
    else:
        amount = order.balance_due

    order.amount_claimed = amount
    order.payment_claimed_at = timezone.now()
    order.save(update_fields=["amount_claimed", "payment_claimed_at"])
    send_payment_claimed_notification(order)
    messages.success(request, "Thanks - we've been notified and will confirm your payment shortly.")
    return redirect("order_detail", pk=order.pk)
