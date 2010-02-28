from decimal import *
from django.conf import settings
from django import template
from django.template.defaultfilters import stringfilter
from currencies.models import Currency


register = template.Library()

def _calculate_price(price, currency):
	try:
		factor = Currency.objects.get(code__exact=currency).factor
	except Currency.DoesNotExist:
		if settings.DEBUG:
			raise Currency.DoesNotExist
		else:
			factor = Decimal('0.0')
	new_price = Decimal(price) * factor
	return new_price.quantize(Decimal('.01'), rounding=ROUND_UP)


@register.filter(name='currency')
@stringfilter
def set_currency(value, arg):
	return _calculate_price(value, arg)

class ChangeCurrencyNode(template.Node):
	def __init__(self, price, currency):
		self.price = template.Variable(price)
		self.currency = template.Variable(currency)

	def render(self, context):
		try:
			return _calculate_price(self.price.resolve(context),
				self.currency.resolve(context))
		except template.VariableDoesNotExist:
			return ''

@register.tag(name='change_currency')
def change_currency(parser, token):
	try:
		tag_name, current_price, new_currency = token.split_contents()
	except ValueError:
		raise template.TemplateSyntaxError, '%r tag requires exactly two arguments' % token.contents.split()[0]
	return ChangeCurrencyNode(current_price, new_currency)
