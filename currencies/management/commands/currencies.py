# -*- coding: utf-8 -*-
from collections import OrderedDict
from importlib import import_module
from django.conf import settings
from django.core.management.base import BaseCommand
from ...models import Currency


# The list of available backend currency sources
sources = OrderedDict([
    # oxr must remain first for backward compatibility
    ('oxr', '._openexchangerates'),
    ('yahoo', '._yahoofinance'),
    #TODO:
    #('google', '._googlecalculator.py'),
    #('ecb', '._europeancentralbank.py'),
])


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
            help=   'Selectively import currencies by supplying the currency codes (e.g. USD) one per switch, '
                    'or supply an uppercase settings variable name with an iterable (once only), '
                    'or looks for settings CURRENCIES or SHOP_CURRENCIES.')

    def get_imports(self, option):
        """
        See if we have been passed a set of currencies or a setting variable
        or look for settings CURRENCIES or SHOP_CURRENCIES.
        """
        if not option:
            for attr in ('CURRENCIES', 'SHOP_CURRENCIES'):
                try:
                    return getattr(settings, attr)
                except AttributeError:
                    continue
            self.stderr.write("Importing all. Some currencies may be out-of-date (MTL) or spurious (XPD)")
            return option
        elif len(option) == 1 and option[0].isupper() and len(option[0]) != 3:
            return getattr(settings, option[0])
        else:
            return [e for e in option if e]

    verbose = 0
    def info(self, msg):
        """Only print if verbose >= 1"""
        if self.verbose:
            self.stdout.write(msg)

    def get_handler(self, options):
        """Return the specified handler"""
        # Import the CurrencyHandler and get an instance
        handler_module = import_module(sources[options[self._source_param]], self._package_name)
        return handler_module.CurrencyHandler(self.info, self.stderr.write)

    def handle(self, *args, **options):
        """Handle the command"""
        # get the command arguments
        self.verbose = int(options.get('verbosity', 0))
        force = options['force']
        imports = self.get_imports(options['import'])

        # Import the CurrencyHandler and get an instance
        handler = self.get_handler(options)

        self.info("Querying database at %s" % handler.endpoint)

        # iterate through the available currency codes
        for code in handler.get_allcurrencycodes():
            if (not imports) or code in imports:
                name = handler.get_currencyname(code)
                if (not Currency._default_manager.filter(code=code)) or force is True:
                    self.info("Creating %r (%s)" % (name, code))

                    obj, created = Currency._default_manager.get_or_create(code=code)
                    if created:
                        Currency._default_manager.filter(pk=obj.pk).update(name=name, is_active=False)

                    if bool(obj.symbol) and force is False:
                        continue

                    symbol = handler.get_currencysymbol(code)
                    if symbol:
                        Currency._default_manager.filter(pk=obj.pk).update(symbol=symbol)
                else:
                    self.info("Skipping %r (%s)" % (name, code))
