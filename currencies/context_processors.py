from currencies.models import Currency


def currencies(request):
    currencies = Currency.objects.all()

    if not request.session.get('currency'):
        request.session['currency'] = Currency.objects.get(is_default__exact=True)

    return {
        'CURRENCIES': currencies,
        'CURRENCY': request.session['currency']
    }
