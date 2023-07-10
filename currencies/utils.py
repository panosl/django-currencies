# -*- coding: utf-8 -*-
from decimal import Decimal as D, InvalidOperation, ROUND_UP
from django.forms.models import model_to_dict
from django.core.cache import cache

from .models import Currency as C
from .conf import SESSION_KEY


def calculate(price, to_code, **kwargs):
    """Converts a price in the default currency to another currency"""

    default_code = get_default_currency()['code']
    return convert(price, default_code, to_code, **kwargs)


def convert(amount, from_code, to_code, decimals=2):
    """Converts from any currency to any currency"""

    if qs is None:
        qs = get_active_currencies_qs()

    qs = get_currencies_dict()

    from_, to = qs[from_code], qs[to_code]

    amount = D(amount) * (to['factor'] / from_['factor'])
    return price_rounding(amount, decimals=decimals)


def get_currency_code(request):
    for attr in ('session', 'COOKIES'):
        if hasattr(request, attr):
            try:
                return getattr(request, attr)[SESSION_KEY]
            except KeyError:
                continue

    return get_default_currency()['code']


def price_rounding(price, decimals=2):
    """Takes a decimal price and rounds to a number of decimal places"""
    try:
        exponent = D('.' + decimals * '0')
    except InvalidOperation:
        # Currencies with no decimal places, ex. JPY, HUF
        exponent = D()
    return price.quantize(exponent, rounding=ROUND_UP)

def get_default_currency():
    currencies = get_currencies_dict()
    for code, cur in currencies.items():
        if cur['is_default']:
            return cur
    return None  # shit happens...


def get_currencies_dict():
    cache_key = 'django-currencies-active'
    result = cache.get(cache_key)
    if result is None:
        # print('--- --- cache not found, DB iterating.....')

        qs = C.active.defer('info').all()

        result = {}
        for cur in qs:
            result[cur.code] = model_to_dict(cur, fields=('code','name','symbol','factor','is_base','is_default',))

        cache.set(cache_key, result, 3600 * 1)  # 1 Hour (This cache var unset on every model change)

    return result


def get_active_currencies_qs():
    return C.active.defer('info').all()