import locale
from urllib.parse import urlencode

from django import template

locale.setlocale(locale.LC_ALL, ('ru', 'UTF-8'))

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context['request'].GET.copy()
    query.update(kwargs)
    return urlencode(query)


@register.filter
def quantity_left(quantity_list, item):
    return quantity_list.count(item)


@register.filter
def get_range_list(count):
    return list(range(count))
