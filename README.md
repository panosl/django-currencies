Introduction
------------

django-currencies allows you to define different currencies, and includes
template tags/filters to allow easy conversion between them.
Usage

Once you have everything set up (read the included INSTALL.txt and
docs/), you will be able to use the following code in your templates:

    {% change_currency [price] [currency_code] %}

    # i.e:

    {% change_currency product.price "USD" %}

    # or if we have the currencies.context_processors.currencies
    # available:

    {% change_currency product.price CURRENCY.code %}

or use the filter:

    {{ [price]|currency:[currency] }}

    # i.e.:

    {{ product.price|currency:"USD" }}

or set the CURRENCY context variable with a POST to the included view:

    {% url currencies_set_currency [currency] %}


OpenExchangeRates integration
-----------------------------

django-currencies has builtin integration with openexchangerates.org.

You will need to specify your API key in your settings file:

    OPENEXCHANGERATES_APP_ID = "c2b2efcb306e075d9c2f2d0b614119ea"

You will then be able to use the management commands "initcurrencies" and "updatecurrencies".
The former will create any currency that exists on openexchangerates.org with a default
factor of 1.0. It is completely optional and does not require an API key. A list of currency codes may be supplied to
limit the currencies that will be initialised.

The updatecurrencies management command will update all your currencies against the rates
returned by openexchangerates.org. Any missing currency will be left untouched.

The updatecurrencysymbols command will add the currency symbol (if missing) to each currency present. Make sure that
your symbol and name columns are set to UTF-8.


Source Code
-----------

The source is kept under git version control at https://github.com/panosl/django-currencies

You can get it by cloning the repository:

    git clone git://github.com/panosl/django-currencies.git


Documentation
-------------

You can browse it online here: http://django-currencies.readthedocs.org/en/latest/


Running Tests
-------------

I'm using nose along with nosedjango

The settings.py is inside the tests/ directory, so you'll need to cd to it, and:

    nosetests -v --with-django
