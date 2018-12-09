#!/usr/bin/env python

import sys
from os import path

import django
from django.conf import settings, global_settings
from django.core.management import execute_from_command_line


MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

if not settings.configured:
    module_root = path.dirname(path.realpath(__file__))

    settings.configure(
        DEBUG = False,
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        },
        TEMPLATES = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'OPTIONS': {
                    'debug': True,
                },
            },
        ],
        INSTALLED_APPS = (
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'currencies',
        ),
        # For django 1.8 to 2.1 compatibility
        MIDDLEWARE = MIDDLEWARE,
        MIDDLEWARE_CLASSES = MIDDLEWARE,
        SITE_ID = 1,
        ROOT_URLCONF = 'currencies.tests.test_urls',
    )

def runtests():
    argv = sys.argv[:1] + ['test'] + sys.argv[1:]
    execute_from_command_line(argv)

if __name__ == '__main__':
    runtests()
