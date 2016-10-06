# -*- coding: utf-8 -*-

import datetime
from decimal import Decimal as D, ROUND_UP

from .models import Currency as C
from .models import DailyCurrencyExchangeRate
from .conf import SESSION_KEY

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def calculate(price, code, date=None, fail_when_no_data=False):
    to = get_daily_exchnge_rate(code, date, fail_when_no_data)
    default = get_daily_exchnge_rate(date=date, fail_when_no_data=fail_when_no_data)

    # First, convert from the default currency to the base currency,
    # then convert from the base to the given currency
    price = (D(price) / default.factor) * to.factor

    return price.quantize(D("0.0001"), rounding=ROUND_UP)


def convert(amount, from_code, to_code, date=None, fail_when_no_data=False):
    if from_code == to_code:
      return amount

    from_ = get_daily_exchnge_rate(from_code, date, fail_when_no_data)
    to = get_daily_exchnge_rate(to_code, date)

    amount = D(amount) * (to.factor / from_.factor)
    return amount.quantize(D("0.0001"), rounding=ROUND_UP)


def get_daily_exchnge_rate(code=None, date=None, fail_when_no_data=False):
    date = date or datetime.date.today()

    query = DailyCurrencyExchangeRate.active\
        .filter(date__lte=date)

    # Select default currency if no code passed
    if code:
        query = query.filter(currency__code=code)
    else:
        query = query.filter(currency__is_default=True)

    try:
        daily_exchange_rate = query.order_by("-date")[0]
    except IndexError:
        raise Exception("Could not find an exchange rate for {code}".format(code=code or "DEFAULT_CURRENCY"))

    if fail_when_no_data and daily_exchange_rate.date < date:
        raise Exception("Could not find an exchange rate for {code} specifically on {date}, but found on {alternative_date}"
            .format(
                code=code,
                date=datetime.date.strftime(date, "%Y-%m-%d"),
                alternative_date=datetime.date.strftime(daily_exchange_rate.date, "%Y-%m-%d")
            )
        )

    return daily_exchange_rate


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


def get_open_exchange_rates_app_id():
    APP_ID = getattr(settings, "OPENEXCHANGERATES_APP_ID", None)
    if APP_ID is None:
        raise ImproperlyConfigured(
            "You need to set the 'OPENEXCHANGERATES_APP_ID' setting to your openexchangerates.org api key")
    return APP_ID