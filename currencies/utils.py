# -*- coding: utf-8 -*-

from decimal import Decimal as D, ROUND_UP
from .models import Currency as C
from .conf import SESSION_KEY


def get_active_currencies_qs():
    return C.active.defer('info').all()


def convert(amount, from_code, to_code, quantize_to=D("0.01"), qs=None):
    if from_code == to_code:
        return amount

    if qs is None:
        qs = get_active_currencies_qs()

    from_, to = qs.get(code=from_code), qs.get(code=to_code)

    amount = D(amount) * (to.factor / from_.factor)
    return amount.quantize(quantize_to, rounding=ROUND_UP)


def calculate(price, to_code, *args, **kwargs):
    try:
        qs = args[1]
    except IndexError:
        qs = kwargs.get('qs', get_active_currencies_qs())
        kwargs['qs'] = qs
    default_code = qs.default().code
    return convert(price, default_code, to_code, *args, **kwargs)


def get_currency_code(request):
    for attr in ('session', 'COOKIES'):
        if hasattr(request, attr):
            try:
                return getattr(request, attr)[SESSION_KEY]
            except KeyError:
                continue

    # fallback to default...
    try:
        return C.active.default().code
    except C.DoesNotExist:
        return None  # shit happens...
