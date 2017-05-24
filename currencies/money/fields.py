# -*- coding: utf-8 -*-
from shop import app_settings
from shop.money.fields import MoneyFieldWidget, MoneyFormField, MoneyField as MoneyFieldBase
from .money_maker import MoneyMaker


class MoneyField(MoneyFieldBase):
    """Override any calls to the CURRENCIES file. isinstance checks the whole inheritance tree, so is okay"""
    def __init__(self, *args, **kwargs):
        self.currency_code = kwargs.pop('currency', app_settings.DEFAULT_CURRENCY)
        self.Money = MoneyMaker(self.currency_code)
        defaults = {
            'max_digits': 30,
            'decimal_places': self.Money._currency[1],
            'default': self.Money(0) if kwargs.get('null', False) else self.Money(),
        }
        defaults.update(kwargs)
        # Skip a level to avoid the call to CURRENCIES from file
        super(MoneyFieldBase, self).__init__(*args, **defaults)

    def deconstruct(self):
        # Skip a level to avoid the call to CURRENCIES from file
        name, path, args, kwargs = super(MoneyFieldBase, self).deconstruct()
        if kwargs['max_digits'] == 30:
            kwargs.pop('max_digits')
        if kwargs['decimal_places'] == self.Money._currency[1]:
            kwargs.pop('decimal_places')
        kwargs.pop('default')
        return name, path, args, kwargs
