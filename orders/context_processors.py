from django.db.models import Sum

from orders.models import Cart


def cart_count(request):
    """{{ cart_count }} available on every page, for the nav cart badge -
    a context processor rather than threading it through every view that
    renders the nav, matching the plain "user is authenticated" checks
    other nav items already rely on."""
    if not request.user.is_authenticated:
        return {"cart_count": 0}
    total = Cart.objects.filter(user=request.user).aggregate(total=Sum("items__quantity"))["total"]
    return {"cart_count": total or 0}
