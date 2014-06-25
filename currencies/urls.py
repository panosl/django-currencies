from django.conf.urls import url, patterns
from currencies.views import set_currency


urlpatterns = patterns('',
    url(r'^setcurrency/$', set_currency,
        name='currencies_set_currency'),
)
