# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns

urlpatterns = patterns('currencies.views',
    url(r'^setcurrency/$', 'set_currency', name='currencies_set_currency'),
)

