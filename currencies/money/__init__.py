# -*- coding: utf-8 -*-
from shop.money import serializers
from .money_maker import MoneyMaker, AbstractMoney

# The default Money type for this shop
Money = MoneyMaker()