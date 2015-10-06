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

3. Be sure you have the ``currencies.context_processors.currencies`` processor:

   .. code-block:: python

       TEMPLATE_CONTEXT_PROCESSORS += (
           'django.core.context_processors.request',  # must be enabled
           'currencies.context_processors.currencies',
       )

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
`openexchangerates.org <http://openexchangerates.org/>`_.

You will need to specify your API key in your settings file:

.. code-block:: python

    OPENEXCHANGERATES_APP_ID = "c2b2efcb306e075d9c2f2d0b614119ea"

You will then be able to use the management commands ``currencies``
and ``updatecurrencies``. The former will import any currencies that
are defined on `openexchangerates.org <http://openexchangerates.org/>`_.
You can selectively import currencies, for example bellow command will
import USD and EUR currencies only:

.. code-block:: shell

    ./manage.py currencies --import=USD --import=EUR

The ``updatecurrencies`` management command will update all your
currencies against the rates returned by `openexchangerates.org <http://openexchangerates.org/>`_.
Any missing currency will be left untouched.

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

License
-------

``django-currencies`` is released under the BSD license.
