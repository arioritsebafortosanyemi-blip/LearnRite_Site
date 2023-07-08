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