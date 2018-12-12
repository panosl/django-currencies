# -*- coding: utf-8 -*-

from django.conf.urls import *
from django.views.generic import TemplateView

urlpatterns = [
    url(r'^currencies/', include('currencies.urls')),
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^context_processor$', TemplateView.as_view(template_name='context_processor.html')),
    url(r'^context_tag$', TemplateView.as_view(template_name='context_tag.html')),
]
