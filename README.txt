Introduction
------------

django-currencies allows you to define different currencies, and includes
template tags/filters to allow easy conversion between them.
Usage

Once you have everything set up (read the included INSTALL.txt and
docs/), you will be able to use the following code in your templates::

   {% change_currency [price] [currency_code] %}

   # i.e:

   {% change_currency product.price "USD" %}

   # or if we have the currencies.context_processors.currencies
   # available:

   {% change_currency product.price CURRENCY.code %}

or use the filter::

   {{ [price]|currency:[currency] }}

   # i.e.:

   {{ product.price|currency:"USD" }}

or set the CURRENCY context variable with a POST to the included view::

    {% url currencies_set_currency [currency] %}


Source Code
-----------

The source is kept under bazaar revision at https://github.com/panosl/django-currencies

You can get it by cloning the repository::

    git://github.com/panosl/django-currencies.git


Documentation
-------------

You can browse it online here: http://readthedocs.org/projects/django-currencies/


Running Tests
-------------

I'm using nose along with nosedjango

The settings.py is inside the tests/ directory, so you'll need to cd to it, and::

    nosetests -v --with-django
