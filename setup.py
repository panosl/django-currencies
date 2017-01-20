#!/usr/bin/env python

import os
import re
import sys
import codecs
import subprocess

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class TestRunner(TestCommand):
    user_options = []

    def run(self):
        raise SystemExit(subprocess.call([sys.executable, 'runtests.py']))


# When creating the sdist, make sure the django.mo file also exists:
if 'sdist' in sys.argv or 'develop' in sys.argv:
    os.chdir('currencies')
    try:
        from django.core import management
        management.call_command('compilemessages', stdout=sys.stderr, verbosity=1)
    except ImportError:
        if 'sdist' in sys.argv:
            raise
    finally:
        os.chdir('..')


def read(*parts):
    file_path = os.path.join(os.path.dirname(__file__), *parts)
    return codecs.open(file_path, encoding='utf-8').read()


def find_version(*parts):
    version_file = read(*parts)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return str(version_match.group(1))
    raise RuntimeError("Unable to find version string.")


setup(
    name='django-currencies',
    version=find_version('currencies', '__init__.py'),
    license='BSD License',

    install_requires=[
        'django>=1.4.2',
        'jsonfield>=1.0.3',
    ],    
    requires=[
        'Django (>=1.4.2)',
        'djangojsonfield (>=1.0.3)',
    ],
    
    description='Adds support for multiple currencies as a Django application.',
    long_description=read('README.rst'),

    author='Panos Laganakos',
    author_email='panos.laganakos@gmail.com',

    maintainer='Basil Shubin',
    maintainer_email='basil.shubin@gmail.com',

    url='https://github.com/panosl/django-currencies',
    download_url='https://github.com/panosl/django-currencies/zipball/master',

    packages=find_packages(exclude=('example*', '*.tests*')),
    include_package_data=True,

    tests_require=[
    ],
    cmdclass={
        'test': TestRunner,
    },
    
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
