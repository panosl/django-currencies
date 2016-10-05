# -*- coding: utf-8 -*-

import datetime
from decimal import Decimal as D
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.exceptions import ImproperlyConfigured

from openexchangerates import OpenExchangeRatesClient

from ...models import Currency, DailyCurrencyExchangeRate
from ...utils import get_open_exchange_rates_app_id


APP_ID = get_open_exchange_rates_app_id()


class Command(BaseCommand):
    help = "Gets / updates exchange rates against the base currency for a specific date."

    option_list = BaseCommand.option_list + (
        make_option('--force', '-f', action='store_true', default=False,
                    help='Import daily rates even if already in database.'
                    ),
        make_option('--date', '-d', default=False,
                    help='Import daily rates even if already in database.',
                    ),
    )

    def handle(self, *args, **options):
        self.verbose = int(options.get('verbosity', 0))
        self.options = options

        if options["date"]:
            date = datetime.datetime.strptime(options["date"], "%Y-%m-%d")
        else:
            date = datetime.date.today()

        if DailyCurrencyExchangeRate.objects.filter(date=date) and not options["force"]:
            raise Exception("Data for %s already retrieved. Use '--force=1' to override." % datetime.date.strftime(date, "%Y-%m-%d"))

        client = OpenExchangeRatesClient(APP_ID)
        if self.verbose >= 1:
            self.stdout.write("Querying database at %s" % (client.ENDPOINT_HISTORICAL))

        try:
            code = Currency._default_manager.get(is_base=True).code
        except Currency.DoesNotExist:
            code = 'USD'  # fallback to default

        l = client.historical(base=code, date=date)

        if self.verbose >= 1 and "timestamp" in l:
            report_datetime = datetime.datetime.fromtimestamp(l["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            self.stdout.write("Rates last updated on %s" % report_datetime)

        if "base" in l:
            if self.verbose >= 1:
                self.stdout.write("All currencies based against %s" % (l["base"]))

            if not Currency._default_manager.filter(code=l["base"]):
                self.stderr.write(
                    "Base currency %r does not exist! Rates will be erroneous without it." % l["base"])
            else:
                base = Currency._default_manager.get(code=l["base"])
                base.is_base = True
                base.save()

        for c in Currency._default_manager.all():
            if c.code not in l["rates"]:
                self.stderr.write("Could not find rates for %s (%s)" % (c, c.code))
                continue

            factor = D(l["rates"][c.code]).quantize(D(".0001"))

            if self.verbose >= 1:
                self.stdout.write("Updating %s rate to %f" % (c, factor))

            exchange_rate = DailyCurrencyExchangeRate.objects\
                .filter(currency=c)\
                .filter(date=date)

            if exchange_rate:
                exchange_rate.update(factor=factor, date=date)
            else:
                DailyCurrencyExchangeRate.objects.create(currency=c, factor=factor, date=date)
