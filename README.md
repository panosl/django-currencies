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


Configuration
-------------

django-currencies has built-in integration with [Open Exchange Rates](http://openexchangerates.org/)

You will need to specify your API key in your settings file:

```python
OPENEXCHANGERATES_APP_ID = "c2b2efcb306e075d9c2f2d0b614119ea"
```

You will then be able to use the management commands ``currencies``
and ``updatecurrencies``. The former will import any currencies that
are defined on [Open Exchange Rates](http://openexchangerates.org/).
You can selectively import currencies, for example bellow command will
import USD and EUR currencies only:

```shell
python ./manage.py currencies --import=USD --import=EUR
```

The ``updatecurrencies`` management command will update all your
currencies against the rates returned by [Open Exchange Rates](http://openexchangerates.org/).
Any missing currency will be left untouched.


Source Code
-----------

The source is kept under git version control at https://github.com/panosl/django-currencies

You can get it by cloning the repository:

    git clone git://github.com/panosl/django-currencies.git


Documentation
-------------

You can browse it online here: http://readthedocs.org/projects/django-currencies/


Running Tests
-------------

I'm using nose along with nosedjango

The settings.py is inside the tests/ directory, so you'll need to cd to it, and:

    nosetests -v --with-django
