from django.contrib import auth
from django.db import models

from store.models import Book


class Cart(models.Model):
    """One cart per account. Individuals never get self-service pricing or
    checkout (see accounts.templatetags.accounts_extras) and institutions
    must always be logged in, so there is no scenario needing a guest/
    session-keyed cart - every cart belongs to exactly one user."""
    user = models.OneToOneField \
        (auth.get_user_model(), on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart({self.user.username})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "book")

    def __str__(self):
        return f"{self.quantity} x {self.book.title}"
