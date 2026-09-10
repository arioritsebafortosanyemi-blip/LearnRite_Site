import random


def random_books(queryset, count):
    """Cheap random sample of `count` books from `queryset`, with contributors
    prefetched. `queryset.order_by('?')` sorts the whole matching table by a
    random value on every request; this instead samples PKs in Python (a
    single cheap index-only query) and fetches only those rows."""
    pks = list(queryset.values_list('pk', flat=True))
    sample_pks = random.sample(pks, min(count, len(pks)))
    return list(queryset.model.objects.filter(pk__in=sample_pks).prefetch_related('contributors'))


def random_book(queryset):
    """Single random book from `queryset`, or None if it's empty."""
    books = random_books(queryset, 1)
    return books[0] if books else None


def average_rating(rating_list):
    if not rating_list:
        return 0
    return round(sum(rating_list)/len(rating_list))

def get_book_price(book, profile):
    """Real price for this profile's declared account type/location, or None if unset."""
    from store.models import BookPrice
    try:
        return book.prices.get(account_type=profile.account_type, location=profile.location).price
    except BookPrice.DoesNotExist:
        return None