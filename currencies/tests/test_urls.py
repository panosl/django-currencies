# -*- coding: utf-8 -*-

from django.urls import re_path, include
from django.views.generic import TemplateView

urlpatterns = [
    re_path(r'^currencies/', include('currencies.urls')),
    re_path(r'^$', TemplateView.as_view(template_name='index.html')),
    re_path(r'^context_processor$', TemplateView.as_view(template_name='context_processor.html')),
    re_path(r'^context_tag$', TemplateView.as_view(template_name='context_tag.html')),
]
