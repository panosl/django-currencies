from __future__ import unicode_literals
import os
from decimal import Decimal, InvalidOperation
from copy import deepcopy

from django import template
from django.test import TestCase, override_settings

from currencies.models import Currency
from currencies.utils import calculate
from currencies.context_processors import currencies as curr_cp


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), 'templates')],
        'APP_DIRS': False,
        'OPTIONS': {
            'debug': True,
        },
    },
]
TEMPLATES_TAG = deepcopy(TEMPLATES)
TEMPLATES_TAG[0]['OPTIONS']['context_processors'] = ['django.template.context_processors.request']
TEMPLATES_CTXPROC = deepcopy(TEMPLATES)
TEMPLATES_CTXPROC[0]['OPTIONS']['context_processors'] = ['currencies.context_processors.currencies']


class UtilsTest(TestCase):
    "Test the utility functions"
    fixtures = ['currencies_test']
    use_transaction = False

    def test_calculate_price_success(self):
        response = calculate('10', 'USD')
        self.assertEqual(response, Decimal('15.00'))

    def test_calculate_price_success_three_decimals(self):
        response = calculate('.5555', 'USD', decimals=3)
        self.assertEqual(response, Decimal('0.834'))

    def test_calculate_price_failure(self):
        self.assertRaises(InvalidOperation, calculate, '1D', 'USD')

    def test_calculate_price_doesnotexist(self):
        self.assertRaises(Currency.DoesNotExist, calculate, '10', 'GBP')


class TemplateTagTest(TestCase):
    "Test the various template tag tools"
    fixtures = ['currencies_test']
    use_transaction = False

    html = """{% load currency %}"""

    def test_currency_filter(self):
        t = template.Template(self.html +
            '{{ 10|currency:"USD" }}'
        )
        self.assertEqual(t.render(template.Context()), '15.00')

    def test_change_currency_tag_success(self):
        t = template.Template(self.html +
            '{% change_currency 10 "USD" %}'
        )
        self.assertEqual(t.render(template.Context()), '15.00')

    def test_change_currency_tag_failure(self):
        t = template.Template(self.html +
            '{% change_currency 10 "GPB" %}'
        )
        self.assertRaises(Currency.DoesNotExist, t.render, template.Context())


class ContextTest(TestCase):
    """
    Test the two methods of retrieving currency context in a template
    and the builtin cookie/session-setting view
    """
    fixtures = ['currencies_test']
    use_transaction = False

    default_render = 'EURUSD\nEUR\nEUR'
    new_render = 'EURUSD\nUSD\nUSD'

    @override_settings(TEMPLATES = TEMPLATES_TAG)
    def test_context_tag(self):
        "Context: template tag"
        self.assertContains(self.client.get('/context_tag'), self.default_render)
        response = self.client.post('/currencies/setcurrency/', {'currency_code': 'USD'})
        self.assertRedirects(response, '/')
        self.assertContains(self.client.get('/context_tag'), self.new_render)

    @override_settings(TEMPLATES = TEMPLATES_CTXPROC)
    def test_context_processor(self):
        "Context: context processor"
        self.assertContains(self.client.get('/context_processor'), self.default_render)
        response = self.client.post('/currencies/setcurrency/', {'currency_code': 'USD'})
        self.assertRedirects(response, '/')
        self.assertContains(self.client.get('/context_processor'), self.new_render)

    @override_settings(TEMPLATES = TEMPLATES)
    def test_context_processor_notexist(self):
        "Context: missing context processor"
        self.assertNotContains(self.client.get('/context_processor'), self.default_render)
        self.assertRaises(KeyError, self.client.get, '/context_tag')
