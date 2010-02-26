from django.test import TestCase
#from django.conf import settings
from django import template
from django.template import loader 
from django.core.management import call_command
from currencies.models import Currency
from decimal import *


class TemplateTagTest(TestCase):
	fixtures = ['test_data.json']
	use_transaction = False

	def setUp(self):
		self.template = '{% load currency %}'

	def test_currency_filter(self):
		t = template.Template(self.template + '{{ 10|currency:"USD" }}')
		c = template.Context()
		s = t.render(c)
		self.assertEqual(s, u'15.0')

	def test_change(self):
		t = template.Template(self.template + '{{ CURRENCY }}')
		c = template.Context()
		s = t.render(c)
		self.assertEqual(s, u'15.0')

	def test_change_currency_tag(self):
		t = template.Template(self.template + '{% change_currency 10 "USD" %}')
		c = template.Context()
		s = t.render(c)
		self.assertEqual(s, u'15.0')
