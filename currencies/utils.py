# -*- coding: utf-8 -*-

from decimal import Decimal as D, ROUND_UP

from .models import Currency as C
from .conf import SESSION_KEY


def calculate(price, code):
    to, default = C.active.get(code=code), C.active.default()

    # First, convert from the default currency to the base currency,
    # then convert from the base to the given currency
    price = (D(price) / default.factor) * to.factor

    return price.quantize(D("0.01"), rounding=ROUND_UP)


def convert(amount, from_code, to_code):
    if from_code == to_code:
      return amount

    from_, to = C.active.get(code=from_code), C.active.get(code=to_code)

    amount = D(amount) * (to.factor / from_.factor)
    return amount.quantize(D("0.01"), rounding=ROUND_UP)


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
