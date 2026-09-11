from django import template

from store.utils import average_rating

register = template.Library()

@register.filter
def remove_colon(value):
    return value.replace(':', '')

@register.filter
def title_2(text):
    text = text.split(' ')
    text_1 = text[0].capitalize()
    return text_1 + ' ' + text[1]

@register.filter
def star_range(rating):
    """List of 5 booleans (filled/empty) for a 0-5 rating, for rendering
    bi-star-fill/bi-star icons without a numeric score on the page."""
    rating = round(rating or 0)
    return [i <= rating for i in range(1, 6)]

@register.simple_tag
def book_rating_summary(book):
    """{'average': int or None, 'count': int} for a book's reviews - reads
    book.review_set.all() rather than aggregating in SQL so it benefits
    from prefetch_related('review_set') the same way contributors/prices
    already do, instead of a query per card."""
    ratings = [review.rating for review in book.review_set.all()]
    if not ratings:
        return {"average": None, "count": 0}
    return {"average": average_rating(ratings), "count": len(ratings)}

@register.simple_tag
def is_wishlisted(book, user):
    """Whether `user` has wishlisted `book`. Caches the user's whole
    wishlisted-book-id set on the user object on first call, so a page
    with 20 cards costs one query total instead of one per card."""
    if not user.is_authenticated:
        return False
    if not hasattr(user, "_wishlisted_book_ids_cache"):
        from accounts.models import WishlistItem
        user._wishlisted_book_ids_cache = set(
            WishlistItem.objects.filter(user=user).values_list("book_id", flat=True)
        )
    return book.pk in user._wishlisted_book_ids_cache