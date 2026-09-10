from orders.models import Cart


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart
