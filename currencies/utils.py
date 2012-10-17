from decimal import Decimal, ROUND_UP
from currencies.models import Currency


def calculate_price(price, currency):
    price = Decimal(price)
    currency = Currency.objects.get(code__exact=currency)
    default = Currency.objects.get(is_default=True)

    # First, convert from the default currency to the base currency
    price = price / default.factor

    # Now, convert from the base to the given currency
    price = price * currency.factor

    return price.quantize(Decimal("0.01"), rounding=ROUND_UP)
