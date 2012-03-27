from django.contrib import admin
from currencies.models import Currency


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('is_default', 'code', 'name', 'symbol', 'factor')
    list_display_links = ('name',)

admin.site.register(Currency, CurrencyAdmin)
