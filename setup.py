#!/usr/bin/env python
from distutils.core import setup
import os
from currencies import __version__


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
	os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('currencies'):
	# Ignore dirnames that start with '.'
	for i, dirname in enumerate(dirnames):
		if dirname.startswith('.'): del dirnames[i]
	if '__init__.py' in filenames:
		pkg = dirpath.replace(os.path.sep, '.')
		if os.path.altsep:
			pkg = pkg.replace(os.path.altsep, '.')
		packages.append(pkg)
	elif filenames:
		prefix = dirpath[13:] # Strip "currencies/" or "currencies\"
		for f in filenames:
			data_files.append(os.path.join(prefix, f))

rst_desc = '''
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

The source is kept under bazaar revision at https://launchpad.net/django-currencies

You can get it by branching or checking it out::

    bzr branch lp:~panosl/django-currencies/trunk

    # or

    bzr co lp:~panosl/django-currencies/trunk 


Documentation
-------------

You can browse it online here: http://packages.python.org/django-currencies/


Running Tests
-------------

I'm using nose along with nosedjango

The settings.py is inside the tests/ directory, so you'll need to cd to it, and::

    nosetests -v --with-django
'''

setup(name='django-currencies',
	version=__version__,
	description='Adds support for multiple currencies as a Django application.',
	long_description=rst_desc,
	author='Panos Laganakos',
	author_email='panos.laganakos@gmail.com',
	url='http://code.google.com/p/django-currencies/',
	package_dir={'currencies': 'currencies'},
	packages=packages,
	package_data={'currencies': data_files},
	classifiers=['Development Status :: 4 - Beta',
		'Environment :: Web Environment',
		'Framework :: Django',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: BSD License',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Topic :: Utilities'],
	)
