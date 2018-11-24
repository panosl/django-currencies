"""
Updatecurrencies tests:
Positive:
    update all: no base & no variables & db base unset | ditto, db base set | -base GBP
    change base with default setting variables CURRENCIES_BASE (1) & SHOP_DEFAULT_CURRENCY (2): 1 | 2 | both
    change base with
Negative:
    No APP_ID
    No connectivity
    Source down
    Base variable which does not exist
    Empty base switch
    Unavailable currency
"""
from __future__ import unicode_literals
import re
from decimal import Decimal
from datetime import datetime, timedelta
from functools import wraps
from django import template
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.utils.six import StringIO
from currencies.models import Currency
from currencies.utils import calculate


default_settings = {
    "OPENEXCHANGERATES_APP_ID": "c2b2efcb306e075d9c2f2d0b614119ea",
}


def fromisoformat(s):
    """
    Hacky way to recover a datetime from an isoformat() string
    Python 3.7 implements datetime.fromisoformat() which is the proper way
    There are many other 3rd party modules out there, but should be good enough for testing
    """
    return datetime(*map(int, re.findall('\d+', s)))


class BaseTestMixin(object):
    "Base test suite mixin"
    source_arg = []

    _code_0dp = 'JPY'
    _code_2dp = 'GBP'
    _code_3dp = 'KWD'
    _newcodes = [_code_0dp, _code_2dp, _code_3dp]
    _code_exist = 'USD'
    _now_delta = timedelta(seconds=1)

    def run_cmd_verify_stdout(self, min_lines, cmd, *args, **kwargs):
        "Runs the given command with full verbosity and checks there are output strings"
        kwargs.setdefault('verbosity', 3)
        buf = StringIO()
        call_command(cmd, stdout=buf, stderr=buf, *args, **kwargs)
        output = buf.getvalue().splitlines()
        buf.close()
        self.assertGreaterEqual(len(output), min_lines)

    def _verify_new_currencies(func):
        """
        Wrapper for testing commands that add new currencies
        Django 1.11 introduced queryset difference(). This would be a better way to implement these tests
        """
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            before_qs = Currency.objects.all()
            before_rows = len(before_qs)
            before_codes = set(record.code for record in before_qs)
            runtime = datetime.now()

            # The command that creates the currencies
            func(inst, *args, **kwargs)

            after_qs = Currency.objects.all()
            after_rows = len(after_qs)
            after_codes = set(record.code for record in after_qs)
            new_codes = after_codes - before_codes
            # There are some new entries
            inst.assertGreater(len(new_codes), 0)
            for code in new_codes:
                record = after_qs.get(code=code)
                # There is a name on each entry
                inst.assertTrue(record.name)
                # Some common codes have symbols
                if code in inst._newcodes:
                    inst.assertTrue(record.symbol)
                # `Created` and `Modified` dates are approx now()
                inst.assertAlmostEqual(runtime, fromisoformat(record.info['Created']), delta=inst._now_delta)
                inst.assertAlmostEqual(runtime, fromisoformat(record.info['Modified']), delta=inst._now_delta)
        return wrapper

    def _verify_new_currency(currency_code):
        "Wrapper for testing a single added currency"
        def decorator(func):
            @wraps(func)
            def wrapper(inst, *args, **kwargs):
                inst.assertRaises(Currency.DoesNotExist, Currency.objects.get, code=currency_code)
                func(inst, *args, *kwargs)
                inst.assertIs(Currency.objects.filter(code=currency_code).exists(), True)
            return wrapper
        return decorator

    ### TESTS FOR SOURCES THAT SUPPORT IMPORTING NEW CURRENCIES ###
    ## POSITIVE Tests ##
    # Info: Minimal tests that all sources support must start with 'test' here
    @_verify_new_currencies
    def test_import_all_currencies_bydefault(self):
        "No parameters imports all currencies"
        self.run_cmd_verify_stdout(20, 'currencies', *self.source_arg)

    @_verify_new_currencies
    def test_import_all_currencies_byemptysetting(self):
        "Empty CURRENCIES setting imports all currencies"
        with self.settings(CURRENCIES=[]):
            self.run_cmd_verify_stdout(20, 'currencies', *self.source_arg)

    @_verify_new_currency(_code_0dp)
    @_verify_new_currencies
    def test_import_variable_CURRENCIES(self):
        "CURRENCIES setting works"
        with self.settings(CURRENCIES=[self._code_0dp]):
            self.run_cmd_verify_stdout(2, 'currencies', *self.source_arg)

    @_verify_new_currency(_code_2dp)
    @_verify_new_currencies
    def test_import_variable_SHOP_CURRENCIES(self):
        "SHOP_CURRENCIES setting works"
        with self.settings(SHOP_CURRENCIES=[self._code_2dp]):
            self.run_cmd_verify_stdout(2, 'currencies', *self.source_arg)

    @_verify_new_currency(_code_0dp)
    @_verify_new_currencies
    def test_import_variable_BOTH(self):
        "CURRENCIES is given priority"
        with self.settings(SHOP_CURRENCIES=[self._code_2dp], CURRENCIES=[self._code_0dp]):
            self.run_cmd_verify_stdout(2, 'currencies', *self.source_arg)
        self.assertRaises(Currency.DoesNotExist, Currency.objects.get, code=self._code_2dp)

    @_verify_new_currency(_code_3dp)
    @_verify_new_currencies
    def test_import_variable_WIBBLE(self):
        "Custom setting variable works"
        with self.settings(WIBBLE=[self._code_3dp]):
            self.run_cmd_verify_stdout(2, 'currencies', *self.source_arg, '--import=WIBBLE')

    @_verify_new_currency(_code_0dp)
    @_verify_new_currencies
    def test_import_single_currency_long(self):
        "Long import syntax"
        self.run_cmd_verify_stdout(2, 'currencies', *self.source_arg, '--import=' + self._code_0dp)

    @_verify_new_currency(_code_2dp)
    @_verify_new_currencies
    def test_import_single_currency_short(self):
        "Short import syntax"
        self.run_cmd_verify_stdout(2, 'currencies', *self.source_arg, '-i=' + self._code_2dp)

    @_verify_new_currency(_code_0dp)
    @_verify_new_currency(_code_2dp)
    @_verify_new_currency(_code_3dp)
    @_verify_new_currencies
    def test_import_single_currencies_mix(self):
        "Mix of import syntax"
        self.run_cmd_verify_stdout(3, 'currencies', *self.source_arg,
            '--import=' + self._code_3dp, '-i=' + self._code_2dp, '-i=' + self._code_0dp)

    def test_skip_existing_currency(self):
        "Skip existing currency"
        before = Currency.objects.get(code=self._code_exist)
        self.run_cmd_verify_stdout(2, 'currencies', *self.source_arg, '-i=' + self._code_exist)
        after = Currency.objects.get(code=self._code_exist)
        self.assertEqual(before.name, after.name)
        self.assertEqual(before.symbol, after.symbol)
        self.assertEqual(before.factor, after.factor)
        self.assertEqual(before.info, after.info)

    def test_force_existing_currency(self):
        "Overwrite existing currency"
        before = Currency.objects.get(code=self._code_exist)
        runtime = datetime.now()
        self.run_cmd_verify_stdout(2, 'currencies', *self.source_arg, '--force', '-i=' + self._code_exist)
        after = Currency.objects.get(code=self._code_exist)
        self.assertNotEqual(before.info, after.info)
        self.assertAlmostEqual(runtime, fromisoformat(after.info['Modified']), delta=self._now_delta)

    ## NEGATIVE Tests ##
#    No APP_ID
#    No connectivity
#    Source down with | without cache
#    Import variable which does not exist
#    Empty import switch
#    Unavailable currency
#class IncSymbolsMixin(object):
    #def inc_symbols(self):
#class ExcSymbolsMixin(object):
    #def exc_symbols(self):
#class IncInfoMixin(object):
    #def inc_info(self):
#class ExcInfoMixin(object):
    #def exc_info(self):
#class IncRatesMixin(object):
#    "For sources that support exchange rates"
    #def inc_rates(self):
#class ExcRatesMixin(object):
#    "For sources that do not support exchange rates"
    #def exc_rates(self):



@override_settings( **default_settings )
class DefaultTest(TestCase, BaseTestMixin):
    "Test Openexchangerates support: the default source"
    fixtures = ['currencies_test']


class OpenExchangeRatesTest(DefaultTest):
    "Test Openexchangerates support: when specified"
    source_arg = ['oxr']


@override_settings( **default_settings )
class YahooTest(TestCase, BaseTestMixin):
    "Test Yahoo support"
    fixtures = ['currencies_test']
    source_arg = ['yahoo']


@override_settings( **default_settings )
class ISOTest(TestCase, BaseTestMixin):
    "Test Currency ISO support"
    fixtures = ['currencies_test']
    source_arg = ['iso']
