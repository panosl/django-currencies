import json
from datetime import datetime
from decimal import Decimal
from urllib2 import urlopen
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import CommandError, NoArgsCommand
from currencies.models import Currency

OPENEXCHANGERATES_APP_ID = getattr(settings, "OPENEXCHANGERATES_APP_ID", None)
if not OPENEXCHANGERATES_APP_ID:
	raise ImproperlyConfigured("You need to set the OPENEXCHANGERATES_APP_ID setting to your openexchangerates.org api key")

CURRENCY_API_URL = "http://openexchangerates.org/latest.json?app_id=%s" % (OPENEXCHANGERATES_APP_ID)


class Command(NoArgsCommand):
	help = "Update the currencies against the current exchange rates"

	def handle_noargs(self, **options):
		print("Querying currencies at %s" % (CURRENCY_API_URL))
		api = urlopen(CURRENCY_API_URL)
		d = json.loads(api.read())

		if "timestamp" in d:
			print("Rates last updated on %s" % (datetime.fromtimestamp(d["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")))

		if "base" in d:
			print("All currencies based against %s" % (d["base"]))
			try:
				base = Currency.objects.get(code=d["base"])
				base.is_base = True
				base.save()
			except Currency.DoesNotExist:
				print("Warning: Base currency %r does not exist! Rates will be erroneous without it." % (d["base"]))
		i = 0

		for currency in Currency.objects.all():
			if currency.code not in d["rates"]:
				print("Warning: Could not find rates for %s (%s)" % (currency, currency.code))
				continue

			rate = Decimal(d["rates"][currency.code]).quantize(Decimal(".0001"))
			if currency.factor != rate:
				print("Updating %s rate to %f" % (currency, rate))
				currency.factor = rate
				currency.save()
				i += 1

		if i == 1:
			print("%i currency updated" % (i))
		else:
			print("%i currencies updated" % (i))
