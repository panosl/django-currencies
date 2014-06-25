import json
import os
from django.core.management.base import NoArgsCommand
from currencies.models import Currency


class Command(NoArgsCommand):
	help = "Update the currency symbols for currently installed currencies"
	def handle_noargs(self, **options):
		rel_path = "./currencies.json"
		abs_file_path = os.path.join(os.path.dirname(__file__), rel_path)
		mappings = {}

		with open(abs_file_path) as df:
			mappings = json.load(df)
		i = 0
		for currency in Currency.objects.all():
			if not currency.symbol:
				symbol = mappings.get(currency.code)
				if symbol:
					currency.symbol = symbol
					currency.save()
					i+=1

		if i == 1:
			print("Updated %i symbol" % (i))
		else:
			print("Updated %i symbols" % (i))
