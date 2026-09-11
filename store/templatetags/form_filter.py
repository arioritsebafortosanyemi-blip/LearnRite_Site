from django import template

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