import random


def random_books(queryset, count):
    """Cheap random sample of `count` books from `queryset`, with contributors
    and prices prefetched. `queryset.order_by('?')` sorts the whole matching
    table by a random value on every request; this instead samples PKs in
    Python (a single cheap index-only query) and fetches only those rows."""
    pks = list(queryset.values_list('pk', flat=True))
    sample_pks = random.sample(pks, min(count, len(pks)))
    return list(queryset.model.objects.filter(pk__in=sample_pks).prefetch_related('contributors', 'prices'))


def random_book(queryset):
    """Single random book from `queryset`, or None if it's empty."""
    books = random_books(queryset, 1)
    return books[0] if books else None


def average_rating(rating_list):
    if not rating_list:
        return 0
    return round(sum(rating_list)/len(rating_list))

def get_book_price(book, profile):
    """Real price for this profile's declared account type/location, or None
    if unset. Iterates `book.prices.all()` rather than `.get(...)` so a
    caller that prefetched prices (there are only ever 4 rows per book)
    doesn't pay a query per book when pricing a whole page of cards."""
    for book_price in book.prices.all():
        if book_price.account_type == profile.account_type and book_price.location == profile.location:
            return book_price.price
    return None