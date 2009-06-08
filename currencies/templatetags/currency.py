from decimal import *
from django import template
from django.template import resolve_variable
from currencies.models import Currency


register = template.Library()

@register.filter(name='currency')
def set_currency(value, arg):
	return Currency.objects.get(code__exact=arg).factor * value

class ChangeCurrencyNode(template.Node):
	def __init__(self, current_price, new_currency):
		self.current_price = current_price
		self.new_currency = new_currency

	def render(self, context):
		try:
			price = resolve_variable(self.current_price, context)
			currency = resolve_variable(self.new_currency, context)
			try:
				factor = Currency.objects.get(code__exact=currency).factor
			except DoesNotExist:
				# if the currency does not exist, avoid breaking the page
				# just give the same price.
				factor = 1.0

			new_price = price * factor

			return str(new_price.quantize(Decimal('.01'), rounding=ROUND_UP))
		except template.VariableDoesNotExist:
			return ''

@register.tag(name='change_currency')
def change_currency(parser, token):
	try:
		tag_name, current_price, new_currency = token.split_contents()
	except ValueError:
		raise template.TemplateSyntaxError, '%r tag requires exactly two arguments' % token.contents.split()[0]
	return ChangeCurrencyNode(current_price, new_currency)
