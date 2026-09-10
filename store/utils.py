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