from django.contrib import auth
from django.db import models

from store.models import Book, BookPrice


class Profile(models.Model):
    """Extra account info every user gets - which price tier and location
    they buy at, self-declared, no verification."""
    user = models.OneToOneField \
        (auth.get_user_model(), on_delete=models.CASCADE, related_name="profile")
    account_type = models.CharField \
        (choices=BookPrice.AccountType.choices, max_length=20,
         default=BookPrice.AccountType.INDIVIDUAL,
         help_text="Self-declared. No verification is performed.")
    location = models.CharField \
        (choices=BookPrice.Location.choices, max_length=20,
         default=BookPrice.Location.LAGOS,
         help_text="Self-declared, used for pricing and delivery.")
    phone_number = models.CharField(max_length=20, blank=True)
    profile_confirmed = models.BooleanField \
        (default=False,
         help_text="Whether the customer has explicitly chosen account_type/location "
                    "(as opposed to still sitting on the signal-created defaults, e.g. "
                    "right after a Google sign-up).")

    def __str__(self):
        return f"{self.user.username} ({self.account_type}/{self.location})"


class Address(models.Model):
    user = models.ForeignKey \
        (auth.get_user_model(), related_name="addresses", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Nigeria")
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name}, {self.city}, {self.state}"


class WishlistItem(models.Model):
    """A saved-for-later book. Open to any logged-in account, unlike cart/
    checkout - individuals can't buy but can still save books to ask about."""
    user = models.ForeignKey \
        (auth.get_user_model(), related_name="wishlist_items", on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
