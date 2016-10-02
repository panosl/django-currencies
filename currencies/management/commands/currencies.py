# -*- coding: utf-8 -*-
import os
import json
from collections import OrderedDict
from importlib import import_module
from django.core.management.base import BaseCommand
from ...models import Currency


# The list of available backend currency sources
sources = OrderedDict([
    # oxr must remain first for backward compatibility
    ('oxr', '._openexchangerates'),
    ('yahoo', '._yahoofinance'),
    #('google', '._googlecalculator.py'),
    #('ecb', '._europeancentralbank.py'),
])


symbols = None
def get_symbol(code):
    """Retrieve the currency symbol from the local file"""
    global symbols
    if not symbols:
        symbolpath = os.path.join(os.path.dirname(__file__), 'currencies.json')
        with open(symbolpath) as df:
            symbols = json.load(df)
    return symbols.get(code)


class Command(BaseCommand):
    help = "Create all missing db currencies available from the chosen source"

    _package_name = __loader__.name.rsplit('.', 1)[0]
    _source_param = 'source'
    _source_default = next(iter(sources))
    _source_kwargs = {'action': 'store', 'nargs': '?', 'default': _source_default,
                        'choices': sources.keys(),
                        'help': 'Select the desired currency rate source, default is ' + _source_default}

    def add_arguments(self, parser):
        """Add command arguments"""
        parser.add_argument(self._source_param, **self._source_kwargs)
        parser.add_argument('--force', '-f', action='store_true', default=False,
            help='Update database even if currency already exists')
        parser.add_argument('--import', '-i', action='append', default=[],
            help='Selectively import currencies (e.g. USD). Default imports all. Specify switch multiple times.')

    def import_source(self, key):
        """Retrieve the source functions"""
        source = import_module(sources[key], self._package_name)
        self.get_handle = source.get_handle
        self.get_allcurrencycodes = source.get_allcurrencycodes
        self.get_currencyname = source.get_currencyname
        self.get_ratetimestamp = source.get_ratetimestamp
        self.get_ratefactor = source.get_ratefactor
        self.remove_cache = source.remove_cache

    def handle(self, *args, **options):
        """Handle the command"""
        # get the command arguments
        self.import_source(options[self._source_param])
        verbose = int(options.get('verbosity', 0))
        force = options['force']
        imports = [e for e in options['import'] if e]

        # get a handle for the connection
        handle, endpoint = self.get_handle(self.stdout.write, self.stderr.write)
        if verbose >= 1:
            self.stdout.write("Querying database at %s" % endpoint)

        # iterate through the available currency codes
        for code in self.get_allcurrencycodes(handle):
            if (not imports) or code in imports:
                name = self.get_currencyname(handle, code)
                if (not Currency._default_manager.filter(code=code)) or force is True:
                    if verbose >= 1:
                        self.stdout.write("Creating %r (%s)" % (name, code))

                    obj, created = Currency._default_manager.get_or_create(code=code)
                    if created:
                        Currency._default_manager.filter(pk=obj.pk).update(name=name, is_active=False)

                    if bool(obj.symbol) and force is False:
                        continue

                    symbol = get_symbol(code)
                    if symbol:
                        Currency._default_manager.filter(pk=obj.pk).update(symbol=symbol)
                else:
                    if verbose >= 1:
                        self.stdout.write("Skipping %r (%s)" % (name, code))
        self.remove_cache()
