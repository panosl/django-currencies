# -*- coding: utf-8 -*-

from django import template
from django.template.defaultfilters import stringfilter

from currencies.models import Currency
from currencies.utils import get_currency_code, calculate

register = template.Library()


class ChangeCurrencyNode(template.Node):

    def __init__(self, price, currency):
        self.price = template.Variable(price)
        self.currency = template.Variable(currency)

    def render(self, context):
        try:
            return calculate(self.price.resolve(context), self.currency.resolve(context))
        except template.VariableDoesNotExist:
            return ''


@register.tag(name='change_currency')
def change_currency(parser, token):
    try:
        tag_name, current_price, new_currency = token.split_contents()
    except ValueError:
        tag_name = token.contents.split()[0]
        raise template.TemplateSyntaxError(
            """%r tag requires exactly two arguments""" % tag_name)
    return ChangeCurrencyNode(current_price, new_currency)


@stringfilter
@register.filter(name='currency')
def do_currency(price, code):
    return calculate(price, code)
