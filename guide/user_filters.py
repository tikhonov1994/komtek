import datetime
import locale
from urllib.parse import urlencode

from django import template

locale.setlocale(locale.LC_ALL, ('ru', 'UTF-8'))

register = template.Library()


@register.filter
def add_placeholder(field, arg):
    return field.as_widget(attrs={'placeholder': arg})


@register.filter
def add_class(field, arg):
    return field.as_widget(attrs={'class': arg})


@register.filter
def input_barcode_filter(field, arg):
    return field.as_widget(attrs={
        'id': arg,
        'class': 'form-control'
    })


@register.filter
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


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


@register.filter
def remainder_of_division(count):
    if count % 10 == 1:
        return True
    return False


@register.filter
def convert_data(string):
    date = datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ")
    return date.strftime('%d %B %Y %H:%M:%S')
