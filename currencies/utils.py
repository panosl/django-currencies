from decimal import *
from django.conf import settings
from currencies.models import Currency


def calculate_price(price, currency):
    try:
        factor = Currency.objects.get(code__exact=currency).factor
    except Currency.DoesNotExist:
        if settings.DEBUG:
            raise Currency.DoesNotExist
        else:
            factor = Decimal('0.0')
    new_price = Decimal(price) * factor
    return new_price.quantize(Decimal('.01'), rounding=ROUND_UP)
