import json
from urllib2 import urlopen
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError, NoArgsCommand
from currencies.models import Currency

CURRENCY_API_URL = "http://openexchangerates.org/currencies.json"


class Command(NoArgsCommand):
	help = "Create all missing currencies defined on openexchangerates.org"

	def handle_noargs(self, **options):
		print("Querying database at %s" % (CURRENCY_API_URL))
		api = urlopen(CURRENCY_API_URL)
		d = json.loads(api.read())
		i = 0

		for currency in sorted(d.keys()):
			if not Currency.objects.filter(code=currency):
				print("Creating %r (%s)" % (d[currency], currency))
				Currency(code=currency, name=d[currency], factor=1.0, is_active=False).save()
				i+=1

		if i == 1:
			print("%i new currency" % (i))
		else:
			print("%i new currencies" % (i))
