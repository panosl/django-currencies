# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from decimal import Decimal, InvalidOperation
from currencies.models import Currency
from currencies.utils import convert
from shop import settings as shop_settings
from shop.money import MoneyMaker as MoneyMakerBase, AbstractMoney as AbstractMoneyBase

"""
Currency conversion extension for django_shop MoneyMaker
Requires:
1. ISO4217Exponent and symbol populating using ``manage.py currencies iso``
   (This automatically imports the currencies set in the SHOP_CURRENCIES setting)
2. Currency factors populating using ``manage.py updatecurrencies <source>``
   (This also sets the base currency to SHOP_DEFAULT_CURRENCY)
3. Some currencies set to active in the admin interface
"""

class classproperty(object):
    """Taken from cms.utils.helpers"""
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


class AbstractMoney(AbstractMoneyBase):
    """Replaces the file-based shop iso4217 CURRENCIES dict"""
    def __reduce__(self):
        """Required for pickling type"""
        return _make_money, (self._currency_code, Decimal.__str__(self))

    @classproperty
    def subunits(cls):
        return 10**cls._currency[1]

    def to(self, new_code):
        """Currency conversion method which takes a valid currency code and returns a new currency object"""
        new_type = MoneyMaker(new_code)
        amount = convert(self.as_decimal(), self._currency_code, new_type._currency_code, new_type._cents)
        return new_type(amount)

    def is_default(self):
        """Whether this is the default currency type"""
        return self._instance.is_default

    def is_base(self):
        """Whether this is the base currency type"""
        return self._instance.is_base


class MoneyMaker(MoneyMakerBase):
    """Enhances the existing MoneyMaker with currency conversion"""
    def __new__(cls, currency_code=None):
        def new_money(cls, value='NaN', context=None):
            """
            Build a class named MoneyIn<currency_code> inheriting from Decimal.
            """
            if isinstance(value, cls):
                assert cls._currency_code == value._currency_code, "Money type currency mismatch"
            if value is None:
                value = 'NaN'
            try:
                self = Decimal.__new__(cls, value, context)
            except Exception as err:
                raise ValueError(err)
            return self

        if currency_code is None:
            currency_code = shop_settings.DEFAULT_CURRENCY
        else:
            currency_code = currency_code.upper()

        try:
            currency = Currency.active.get(code=currency_code)
        except Currency.DoesNotExist:
            raise ValueError("'{}' is not in the active list of currencies. Have a look in the Currencies section of the admin interface.".format(currency_code))
        name = str('MoneyIn' + currency_code)
        bases = (AbstractMoney,)

        exp = currency.info['ISO4217Exponent']
        try:
            cents = Decimal('.' + exp * '0')
        except InvalidOperation:
            # Currencies with no decimal places, ex. JPY, HUF
            cents = Decimal()

        # original is a 4-tuple of 0 iso number, 1 exponent, 2 symbol & 3 translated name
        currency_vals = (   currency.info['ISO4217Number'],
                            exp,
                            currency.symbol,
                            _(currency.name) )
        attrs = {   '_currency_code': currency_code,
                    '_currency': currency_vals,
                    '_cents': cents,
                    '__new__': new_money,
                    # new attribute
                    '_instance': currency
                }
        new_class = type(name, bases, attrs)
        return new_class



def _make_money(currency_code, value):
    """
    Function which curries currency and value
    """
    return MoneyMaker(currency_code)(value)
