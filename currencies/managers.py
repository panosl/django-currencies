# -*- coding: utf-8 -*-

from django.db import models


class CurrencyManager(models.Manager):

    def get_query_set(self):
        return super(CurrencyManager, self).get_query_set().filter(
            is_active=True)

    def default(self):
        return self.get(is_default=True)

    def base(self):
        return self.get(is_base=True)
