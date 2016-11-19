# -*- coding: utf-8 -*-

from decimal import Decimal as D, ROUND_UP
from .models import Currency as C
from .conf import SESSION_KEY



def convert(amount, from_code, to_code, quantize_to=D("0.01")):
    if from_code == to_code:
      return amount

    from_, to = C.active.get(code=from_code), C.active.get(code=to_code)

    amount = D(amount) * (to.factor / from_.factor)
    return amount.quantize(quantize_to, rounding=ROUND_UP)


def calculate(price, *args, **kwargs):
    default_code = C.active.default().code
    return convert(price, default_code, *args, **kwargs)


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
