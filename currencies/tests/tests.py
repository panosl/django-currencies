from decimal import *
from django.test import TestCase
from django.conf import settings
from django import template
from currencies.models import Currency


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
