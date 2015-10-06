# -*- coding: utf-8 -*-

from django import template
from django.template.defaultfilters import stringfilter

from classytags.core import Tag, Options
from classytags.arguments import Argument

from ..models import Currency
from ..utils import get_currency_code, calculate

register = template.Library()


    options = Options(
        'as',
        Argument('varname', resolve=False, required=False),
    )

    def render_tag(self, context, varname):
        if varname:
            return ''
        else:



class ChangeCurrencyTag(Tag):
    name = 'change_currency'
    options = Options(
        Argument('price', resolve=True, required=True),
        Argument('code', resolve=True, required=True),
    )

    def render_tag(self, context, price, code):
        return calculate(price, code)

register.tag(ChangeCurrencyTag)


@stringfilter
@register.filter(name='currency')
def do_currency(price, code):
    return calculate(price, code)
