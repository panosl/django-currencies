from django.contrib import admin
from currencies.models import Currency


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("name", "is_default", "code", "symbol", "factor")
    search_fields = ("name", "code")

admin.site.register(Currency, CurrencyAdmin)
