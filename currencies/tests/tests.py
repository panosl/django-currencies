from decimal import *
from django.test import TestCase
from django.conf import settings
from django import template
from currencies.models import Currency
from currencies.utils import calculate_price


class UtilsTest(TestCase):
    fixtures = ['test_data.json']
    use_transaction = False

    def test_calculate_price_success(self):
        res = calculate_price('10', 'USD')
        self.assertEqual(res, Decimal('15.00'))

    def test_calculate_price_fail(self):
        res = calculate_price('10', 'GBP')
        self.assertEqual(res, Decimal('0.00'))

    def test_calculate_price_currency_doesnotexist(self):
        settings.DEBUG = True
        self.assertRaises(Currency.DoesNotExist, calculate_price, '10', 'GBP')
        settings.DEBUG = False


class TemplateTagTest(TestCase):
    fixtures = ['test_data.json']
    use_transaction = False

    def setUp(self):
        self.template = '{% load currency %}'

    def test_currency_filter(self):
        t = template.Template(self.template +
            '{{ 10|currency:"USD" }}'
        )
        c = template.Context()
        s = t.render(c)
        self.assertEqual(s, u'15.00')

    def test_change_currency_tag_success(self):
        t = template.Template(self.template +
            '{% change_currency 10 "USD" %}'
        )
        c = template.Context()
        s = t.render(c)
        self.assertEqual(s, u'15.00')

    def test_change_currency_tag_fail(self):
        t = template.Template(self.template +
            '{% change_currency 10 "GPB" %}'
        )
        c = template.Context()
        s = t.render(c)
        self.assertEqual(s, u'0.00')
