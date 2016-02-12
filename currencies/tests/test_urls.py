# -*- coding: utf-8 -*-

from django.conf.urls import *

urlpatterns = [
    url(r'^currencies/', include('currencies.urls')),
]
