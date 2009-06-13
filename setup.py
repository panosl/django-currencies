#!/usr/bin/env python
from distutils.core import setup
import os


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


setup(name='django-currencies',
	version='0.1',
	description='Adds support for multiple currencies as a Django application',
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
