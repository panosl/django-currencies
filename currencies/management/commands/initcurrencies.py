import json
from urllib2 import urlopen
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError, BaseCommand
from currencies.models import Currency

CURRENCY_API_URL = "http://openexchangerates.org/currencies.json"


class Command(BaseCommand):
	help = "Create all missing currencies defined on openexchangerates.org. A list of ISO 4217 codes may be supplied to limit the currencies initialised."
	args = "<code code code code...>"

	def handle(self, *args, **options):
		print("Querying database at %s" % (CURRENCY_API_URL))

		currencies = []
		if len(args):
			currencies = list(args)

		api = urlopen(CURRENCY_API_URL)
		d = json.loads(api.read())
		i = 0

		for currency in sorted(d.keys()):
			if (not currencies) or currency in currencies:
				if not Currency.objects.filter(code=currency):
					print("Creating %r (%s)" % (d[currency], currency))
					Currency(code=currency, name=d[currency], factor=1.0, is_active=False).save()
					i+=1

		if i == 1:
			print("%i new currency" % (i))
		else:
			print("%i new currencies" % (i))