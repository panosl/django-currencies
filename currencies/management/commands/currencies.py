# -*- coding: utf-8 -*-

import os
import json
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.exceptions import ImproperlyConfigured

from openexchangerates import OpenExchangeRatesClient

from ...models import Currency as C

APP_ID = getattr(settings, "OPENEXCHANGERATES_APP_ID", None)
if APP_ID is None:
    raise ImproperlyConfigured(
        "You need to set the 'OPENEXCHANGERATES_APP_ID' setting to your openexchangerates.org api key")


class Command(BaseCommand):
    help = "Create all missing currencies defined on openexchangerates.org."
    
    file_path = os.path.join(os.path.dirname(__file__), 'currencies.json')

    option_list = BaseCommand.option_list + (
        make_option('--force', '-f', action='store_true', default=False,
            help='Import even if currencies are up-to-date.'
        ),
        make_option('--import', '-i', action='append', default=[],
            help='Selectively import currencies (e.g. USD). Default is to process all. Can be used multiple times',
        ),
    )

    def handle(self, *args, **options):
        self.verbose = int(options.get('verbosity', 0))
        self.options = options

        self.force = self.options['force']

        self.imports = [e for e in self.options['import'] if e]

        client = OpenExchangeRatesClient(APP_ID)
        if self.verbose >= 1:
            self.stdout.write("Querying database at %s" % (client.ENDPOINT_CURRENCIES))

        symbols = {}
        with open(self.file_path) as df:
            symbols = json.load(df)

        currencies = client.currencies()
        for code in sorted(currencies.keys()):
            if (not self.imports) or code in self.imports:
                if not C._default_manager.filter(code=code) or self.force is True:
                    if self.verbose >= 1:
                        self.stdout.write("Creating %r (%s)" % (currencies[code], code))

                    c, created = C._default_manager.get_or_create(code=code)
                    if created is True:
                        C._default_manager.filter(pk=c.pk).update(name=currencies[code], is_active=False)

                    if bool(c.symbol) and self.force is False:
                        continue

                    symbol = symbols.get(c.code)
                    if symbol is not None:
                        C._default_manager.filter(pk=c.pk).update(symbol=symbol)
                else:
                    if self.verbose >= 1:
                        self.stdout.write("Skipping %r (%s)" % (currencies[code], code))
