from decimal import Decimal

from django import template
from django.test import TestCase

from currencies.models import Currency
from currencies.utils import calculate


class UtilsTest(TestCase):
    fixtures = ['test_data']
    use_transaction = False

    def test_calculate_price_success(self):
        response = calculate('10', 'USD')
        self.assertEqual(response, Decimal('15.00'))

    # def test_calculate_price_failure(self):
    #     response = calculate('10', 'EUR')
    #     self.assertEqual(response, Decimal('0.00'))

    def test_calculate_price_doesnotexist(self):
        self.assertRaises(
            Currency.DoesNotExist, calculate, '10', 'GBP')


class TemplateTagTest(TestCase):
    fixtures = ['test_data']
    use_transaction = False

    html = """{% load currency %}"""

    def test_currency_filter(self):
        t = template.Template(self.html +
            '{{ 10|currency:"USD" }}'
        )
        self.assertEqual(t.render(template.Context()), u'15.00')

    def test_change_currency_tag_success(self):
        t = template.Template(self.html +
            '{% change_currency 10 "USD" %}'
        )
        self.assertEqual(t.render(template.Context()), u'15.00')

    # def test_change_currency_tag_failure(self):
    #     t = template.Template(self.html +
    #         '{% change_currency 10 "GPB" %}'
    #     )
    #     self.assertEqual(t.render(template.Context()), u'0.00')
