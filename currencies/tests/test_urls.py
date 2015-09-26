# -*- coding: utf-8 -*-

from django.conf.urls import *

urlpatterns = patterns('',
    url(r'^currencies/', include('currencies.urls')),
)
