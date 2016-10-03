# -*- coding: utf-8 -*-
import sys
from decimal import Decimal
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from openexchangerates import OpenExchangeRatesClient, OpenExchangeRatesClientException

# Initialisation
APP_ID = getattr(settings, "OPENEXCHANGERATES_APP_ID", None)
if APP_ID is None:
    raise ImproperlyConfigured(
        "You need to set the 'OPENEXCHANGERATES_APP_ID' setting to your openexchangerates.org api key")

def get_handle(print_info, print_warn):
    """
    Get a handle to the currency client and description string
    Passes helper functions for informational and warning messages
    """
    module = sys.modules[__name__]
    setattr(module, 'info', print_info)
    setattr(module, 'warn', print_warn)
    client = OpenExchangeRatesClient(APP_ID)
    return client, client.ENDPOINT_CURRENCIES

currencies = None
def get_allcurrencycodes(handle):
    """Return an iterable of 3 character ISO 4217 currency codes"""
    global currencies
    currencies = handle.currencies()
    return currencies.keys()

def get_currencyname(handle, code):
    """Return the currency name from the code"""
    if not currencies:
        get_allcurrencycodes(handle)
    return currencies[code]

rates = None
def check_rates(rates, base):
    """Local helper function for validating rates response"""

    if "rates" not in rates:
        raise RuntimeError("OpenExchangeRates: 'rates' not found in results")
    if "base" not in rates or rates["base"] != base or base not in rates["rates"]:
        warn("OpenExchangeRates: 'base' not found in results")

def changebase(rates, current_base, new_base):
    """
    Local helper function for changing currency base, returns new rates
    Defaults to ROUND_HALF_EVEN
    """
    check_rates(rates, current_base)
    if new_base not in rates["rates"]:
        raise RuntimeError("OpenExchangeRates: %s not found in rates whilst changing base" % new_base)

    warn("OpenExchangeRates: changing base ourselves")
    multiplier = Decimal(1) / rates["rates"][new_base]
    for code, rate in rates["rates"].items():
        rates["rates"][code] = (rate * multiplier).quantize(Decimal(".0001"))
    rates["base"] = new_base
    check_rates(rates, new_base)
    return rates

def get_latestcurrencyrates(handle, base):
    """
    Local helper function
    Changing base is only available for paid-for plans, hence we do it ourselves
    """
    global rates
    if not rates:
        try:
            rates = handle.latest(base=base)
            check_rates(rates, base)
        except OpenExchangeRatesClientException as e:
            default_base = 'USD'
            if str(e).startswith('403'):
                rates = changebase(handle.latest(base=default_base), default_base, base)
            else:
                raise

def get_ratetimestamp(handle, base, code):
    """Return rate timestamp in datetime format"""
    get_latestcurrencyrates(handle, base)
    try:
        return datetime.fromtimestamp(rates["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
    except KeyError:
        return None

def get_ratefactor(handle, base, code):
    """Return the Decimal currency exchange rate factor of 'code' compared to 1 'base' unit, or None"""
    get_latestcurrencyrates(handle, base)
    try:
        return Decimal(rates["rates"][code])
    except KeyError:
        return None

def remove_cache():
    """Remove any cached data"""
    global currencies, rates
    currencies = rates = None
