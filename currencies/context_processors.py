# -*- coding: utf-8 -*-

from .models import Currency
from .utils import get_currency_code
from .conf import SESSION_KEY


def currencies(request):
    # make sure that currency was initialized
    if not SESSION_KEY in request.session or request.session.get(SESSION_KEY) is None:
        request.session[SESSION_KEY] = get_currency_code(False)

    return {
        'CURRENCIES': Currency.active.all(),  # get all active currencies
        'CURRENCY_CODE': request.session[SESSION_KEY],
    }
