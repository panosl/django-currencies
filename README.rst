django-currencies
=================

django-currencies allows you to define different currencies, and
includes template tags/filters to allow easy conversion between them.

For more details, see the `documentation <http://django-currencies.readthedocs.org/en/latest/>`_ at Read The Docs.

Authored by `Panos Laganakos <http://panoslaganakos.com/>`_, and some great
`contributors <https://github.com/panosl/django-currencies/contributors>`_.

Installation
------------

1. Either clone this repository into your project, or install with ``pip``:

   .. code-block:: shell

       pip install django-currencies

2. You'll need to add ``currencies`` to ``INSTALLED_APPS`` in your project's settings file:

   .. code-block:: python

       import django

       INSTALLED_APPS += (
           'currencies',
       )

       if django.VERSION < (1, 7):
           INSTALLED_APPS += (
               'south',
           )

3a. Either have the ``currencies.context_processors.currencies`` processor:

   .. code-block:: python

       TEMPLATE_CONTEXT_PROCESSORS += (
           'django.core.context_processors.request',  # must be enabled
           'currencies.context_processors.currencies',
       )

3b. Or use the template tag ``currency_context``:

   .. code-block:: html+django

       {% load currency %}
       {% currency_context %}

4. Update your ``urls.py`` file :

   .. code-block:: python

       urlpatterns += patterns('',
           url(r'^currencies/', include('currencies.urls')),
       )

Then run ``./manage.py syncdb`` to create the required database tables

Please see ``example`` application. This application is used to
manually test the functionalities of this package. This also serves as
a good example.

You need Django 1.4 or above to run that. It might run on older
versions but that is not tested.

Upgrading from 0.3.3
~~~~~~~~~~~~~~~~~~~~

Upgrading from 0.3.3 is likely to cause problems trying to apply a
migration when the tables already exist. In this case a fake migration
needs to be applied:

.. code-block:: shell

    ./manage.py migrate currencies 0001 --fake

Configuration
-------------

django-currencies has built-in integration with
`openexchangerates.org <http://openexchangerates.org/>`_,
`Yahoo Finance <http://finance.yahoo.com/currency-converter/>`_ and
`Currency ISO <http://www.currency-iso.org/>`_.

**Management Commands**

You can use the management commands ``currencies`` and ``updatecurrencies``
to maintain the currencies in the database. The former will import any
currencies that are defined on the selected source. The latter will update
all the database currencies against the rates returned by the source. Any
currency missing on the source will be left untouched.

You can selectively import currencies, for example the commands below
will import USD and EUR currencies only, or use a variable from the
settings that points to an iterable respectively:

.. code-block:: shell

    ./manage.py currencies --import=USD --import=EUR
    ./manage.py currencies -i SHOP_CURRENCIES

The command automatically looks for variables CURRENCIES or SHOP_CURRENCIES
in settings if ``-i`` is not specified.
For more information on the additional switches ``--force`` and ``--verbosity``
try ``./manage.py help currencies``.

``updatecurrencies`` can automatically change the base rate of the imported
exchange rates by specifying the ``--base`` switch like so:

.. code-block:: shell

    ./manage.py updatecurrencies oxr --base=USD
    ./manage.py updatecurrencies yahoo -b SHOP_DEFAULT_CURRENCY

The command automatically looks for variables CURRENCIES_BASE or SHOP_DEFAULT_CURRENCY
in settings if ``-b`` is not specified.

**OpenExchangeRates**

This is the default source or select it specifically using ``oxr`` as
positional argument to either command.

You will need to specify your API key in your settings file:

.. code-block:: python

    OPENEXCHANGERATES_APP_ID = "c2b2efcb306e075d9c2f2d0b614119ea"

Requirements: `requests <http://docs.python-requests.org/en/master/>`_
(python3-compatible fork of `OpenExchangeRatesClient <https://github.com/metglobal/openexchangerates>`_
is integrated due to abandoned project)

**Yahoo Finance**

Select this source by specifying ``yahoo`` as positional argument.

Requirements: `BeautifulSoup4 <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_
and `requests <http://docs.python-requests.org/en/master/>`_

**Currency ISO**

Select this source by specifying ``iso`` as positional argument.

Requirements: `requests <http://docs.python-requests.org/en/master/>`_

===========  ==========  =====  =======  ==========
Integration               Live Feeds
-----------  --------------------------------------
..           Currencies  Rates  Symbols  Other Info
===========  ==========  =====  =======  ==========
    oxr          |T|      |T|
   yahoo         |T|      |T|     |T|       |T|
    iso          |T|              |T|       |T|
===========  ==========  =====  =======  ==========

.. |T| unicode:: U+2705 .. ticked

Other info includes ISO4217 number and exponent, country and city names, and alternative
currency names.

Usage
-----

First of all, load the ``currency`` in every template where you want to use it:

.. code-block:: html+django

    {% load currency %}

Use:

.. code-block:: html+django

    {% change_currency [price] [currency_code] %}
    
for example:

.. code-block:: html+django

    {% change_currency product.price "USD" %}

    <!-- or if you have the ``currencies.context_processors.currencies`` available -->
    {% change_currency product.price CURRENCY.code %}

or use the filter:

.. code-block:: html+django

    {{ [price]|currency:[currency_code] }}

for example:

.. code-block:: html+django

    {{ product.price|currency:"USD" }}

or set the ``CURRENCY_CODE`` context variable with a ``POST`` to the included view:

.. code-block:: html+django

    {% url 'currencies_set_currency' [currency_code] %}

or use the template tag ``currency_context``:

.. code-block:: html+django

    {% currency_context %}

which gives the three context variables: ``CURRENCIES``, ``CURRENCY_CODE`` and ``CURRENCY``.

**Template**

Included is a template for a Bootstrap 3 & fontawesome compatible navbar currency
chooser. The navbar item will display if there are more than 1 active currencies.
There is a navbar parameter ``dropdown_extra_class`` which is used to supply extra classes
to the dropdown:

.. code-block:: html+django

    {% block navbar-nav %}
        ...
        <ul class="nav navbar-nav navbar-right">
            ...
            {% with dropdown_extra_class="collapsed-nav" %}
            {% include "currencies/navbar/currency-chooser-bs3fa.html" %}
            {% endwith %}

.. note::

    The currency choice may not be reflected on the navbar if your view is not re-rendered.
    This may be the case if you are viewing a default page in Django CMS for example.
    This is due to the context processor not being triggered because the RequestContext
    is not re-generated.

License
-------

``django-currencies`` is released under the BSD license.
