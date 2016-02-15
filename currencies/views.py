from django.http import HttpResponseRedirect
from currencies.models import Currency


def set_currency(request):
    if request.method == 'POST':
        currency_code = request.POST.get('currency', None)
        next = request.POST.get('next', None)
    else:
        currency_code = request.GET.get('currency', None)
        next = request.GET.get('next', None)
    if not next:
        next = request.META.get('HTTP_REFERER', None)
    if not next:
        next = '/'
    response = HttpResponseRedirect(next)
    if currency_code:
        if hasattr(request, 'session'):
            try:
                currency = Currency.objects.get(code__iexact=currency_code)
            except Currency.DoesNotExist:
                currency_code = None
                currency = None
            request.session['currency'] = currency
        else:
            response.set_cookie('currency', currency_code)
    return response
