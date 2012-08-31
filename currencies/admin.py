from django.contrib import admin
from currencies.models import Currency


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("name", "is_default", "code", "symbol", "factor")

admin.site.register(Currency, CurrencyAdmin)
