from currencies.models import Currency


def currencies(request):
    currencies = Currency.objects.active()

    if not request.session.get('currency'):
        try:
            currency = Currency.objects.get(is_default__exact=True)
        except Currency.DoesNotExist:
            currency = None
        request.session['currency'] = currency

    return {
        'CURRENCIES': currencies,
        'CURRENCY': request.session['currency']
    }
