# -*- coding: utf-8 -*-
"""
Various test cases for the `currencies` and `updatecurrencies` management commands
"""
from __future__ import unicode_literals
import re, os
from decimal import Decimal
from datetime import datetime, timedelta
from functools import wraps
from unittest.mock import patch, MagicMock
from django import template
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.utils.six import StringIO
from currencies.models import Currency
from currencies.utils import calculate


cwd = os.path.abspath(os.path.dirname(__file__))


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
    "Test suite for functionality supported by all sources"
    source_arg = []

    _code_0dp = 'JPY'
    _symb_0dp = '¥'
    _name_0dp = 'Yen'
    _code_2dp = 'GBP'
    _symb_2dp = '£'
    _name_2dp = 'Pound'
    _code_3dp = 'KWD'
    _symb_3dp = 'د.ك'
    _name_3dp = 'Dinar'
    _newcodes = [_code_0dp, _code_2dp, _code_3dp]
    _newsymbs = [_symb_0dp, _symb_2dp, _symb_3dp]
    _newnames = [_name_0dp, _name_2dp, _name_3dp]
    _code_exist = 'USD'
    _symb_exist = '$'
    _name_exist = 'Dollar'
    _code_base = 'EUR'
    _symb_base = '€'
    _name_base = 'Euro'
    _now_delta = timedelta(seconds=1)

    def run_cmd_verify_stdout(self, min_lines, cmd, *args, **kwargs):
        "Runs the given command with full verbosity and checks there are output strings"
        kwargs.setdefault('verbosity', 3)
        buf = StringIO()
        call_command(cmd, stdout=buf, stderr=buf, *args, **kwargs)
        output = buf.getvalue().splitlines()
        buf.close()
        self.assertGreaterEqual(len(output), min_lines)
        return output

    def default_currency_cmd(self):
        "Single currency import that is reused for a lot of basic tests"
        return self.run_cmd_verify_stdout(2, 'currencies', *self.source_arg, '-i=' + self._code_2dp)

    def default_rate_cmd(self):
        "Rate update command that is reused for a lot of basic tests. Uses the base from the db"
        return self.run_cmd_verify_stdout(3, 'updatecurrencies', *self.source_arg)

    def _verify_stdout_msg(msglist):
        "Ensure one of the messages is in the command stdout"
        def decorator(func):
            @wraps(func)
            def wrapper(inst, *args, **kwargs):
                lines = func(inst, *args, **kwargs)
                output = '\n'.join(lines)
                match = False
                for msg in msglist:
                    if msg in output:
                        match = True
                        break
                inst.assertIs(match, True)
                return lines
            return wrapper
        return decorator

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
            ret = func(inst, *args, **kwargs)

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
            return ret
        return wrapper

    def _verify_new_currency(currency_code):
        "Wrapper for testing a single added currency"
        def decorator(func):
            @wraps(func)
            def wrapper(inst, *args, **kwargs):
                inst.assertRaises(Currency.DoesNotExist, Currency.objects.get, code=currency_code)
                ret = func(inst, *args, **kwargs)
                inst.assertIs(Currency.objects.filter(code=currency_code).exists(), True)
                return ret
            return wrapper
        return decorator

    def _verify_rates(base_code):
        "Wrapper for testing that the rates are not 1.0 after an update"
        def decorator(func):
            @wraps(func)
            def wrapper(inst, *args, **kwargs):
                inst.assertGreater(Currency.objects.update(factor=1.0), 1)
                ret = func(inst, *args, **kwargs)
                after_qs = Currency.objects.all()
                for curr in after_qs.filter(is_base=False):
                    inst.assertNotEqual(curr.factor, 1.0)
                inst.assertEqual(after_qs.get(code=base_code, is_base=True).factor, 1.0)
                return ret
            return wrapper
        return decorator

    def _move_cache_file(modulename):
        "Wrapper for testing the currency cache file. Keeps the newest file with size>0"
        def decorator(func):
            @wraps(func)
            def wrapper(inst, *args, **kwargs):
                from importlib import import_module
                module = import_module(modulename)
                modfile = module.CurrencyHandler._cached_currency_file
                orgfile = os.path.join(os.path.dirname(modfile), '_tempcache')
                os.rename(modfile, orgfile)
                ret = func(inst, *args, **kwargs)
                try:
                    modfileinfo = os.stat(modfile)
                except Exception:
                    os.rename(orgfile, modfile)
                else:
                    if modfileinfo.st_size > 0 and modfileinfo.st_mtime > os.stat(orgfile).st_mtime:
                        os.remove(orgfile)
                    else:
                        os.remove(modfile)
                        os.rename(orgfile, modfile)
                return ret
            return wrapper
        return decorator


    ### TESTS FOR SOURCES THAT SUPPORT IMPORTING NEW CURRENCIES ###
    ## POSITIVE Tests ##
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

# Mock helper function for oxr rates support without a valid API key for testing
def mock_requestsession_getjson(filename):
    "Sets up the mock session instance to return a fixed json rates file"
    def mock_resp_json(*args, **kwargs):
        import json
        with open(filename, 'r') as fp:
            return json.load(fp, *args, **kwargs)
    mocksess = MagicMock()
    sessInst = mocksess.return_value
    resp = sessInst.get.return_value
    resp.raise_for_status.return_value = None
    resp.json.side_effect = mock_resp_json
    return mocksess

# Mock request exception helpers for simulating connectivity problems
def mock_requestsession_getexception():
    "Sets up the mock session instance to raise a Request exception"
    from requests.exceptions import RequestException
    mocksess = MagicMock()
    sessInst = mocksess.return_value
    sessInst.get.side_effect = RequestException('Mocked Exception')
    return mocksess

def mock_requestget_exception():
    "Sets up the mock get instance to raise a Request exception"
    from requests.exceptions import RequestException
    mockget = MagicMock()
    mockget.side_effect = RequestException('Mocked Exception')
    return mockget

@patch('requests.Session', mock_requestsession_getjson('%s/oxr_USD.json' % cwd))
class IncRatesMixin(object):
    "For sources that support exchange rates"

    ## POSITIVE Tests ##
    @BaseTestMixin._verify_rates('USD')
    def test_update_rates_nobase(self):
        "Update currency rates without supplying a base at all - USD"
        base = Currency.objects.update(is_base=False)
        self.default_rate_cmd()

    @BaseTestMixin._verify_rates(BaseTestMixin._code_base)
    def test_update_rates_dbbase(self):
        "Update currency rates with the db base"
        self.default_rate_cmd()

    @BaseTestMixin._verify_rates(BaseTestMixin._code_exist)
    def test_update_rates_specifybase(self):
        "Update currency rates with a specific base"
        before_base = Currency.objects.get(is_base=True).code
        self.run_cmd_verify_stdout(4, 'updatecurrencies', *self.source_arg, '--base=' + self._code_exist)
        after_base = Currency.objects.get(is_base=True).code
        self.assertEqual(self._code_exist, after_base)
        self.assertNotEqual(before_base, after_base)

#    def test_update_rates_variable_CURRENCIES_BASE(self):
#        "Update currency rates using the CURRENCIES_BASE setting variable"

#    def test_update_rates_variable_SHOP_DEFAULT_CURRENCY(self):
#        "Update currency rates using the SHOP_DEFAULT_CURRENCY setting variable"

#    def test_update_rates_variable_BOTH(self):
#        "Update currency rates with both builtin setting variables"

#    def test_update_rates_variable_WIBBLE(self):
#        "Update currency rates using the WIBBLE setting variable"
#    update all: no base & no variables & db base unset | ditto, db base set | -base GBP
#    change base with default setting variables CURRENCIES_BASE (1) & SHOP_DEFAULT_CURRENCY (2): 1 | 2 | both

    ## NEGATIVE Tests ##
#    No connectivity
#    Source down
#    Base variable which does not exist
#    Empty base switch
#    Specific base which does not exist in the db
#    Unavailable currency

class ExcRatesMixin(object):
    "For sources that do not support exchange rates"

    @BaseTestMixin._verify_stdout_msg(['source does not provide currency rate information', 'Deprecated'])
    def test_update_rates(self):
        "Rates not supported"
        return self.default_rate_cmd()


### ACTUAL TEST CLASSES ###

@override_settings( **default_settings )
class DefaultTest(IncRatesMixin, BaseTestMixin, TestCase):
    "Test Openexchangerates support: the default source"
    fixtures = ['currencies_test']

    @override_settings()
    def test_missing_APP_ID_currencies(self):
        "No APP_ID - currencies"
        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured
        del settings.OPENEXCHANGERATES_APP_ID
        self.assertRaises(ImproperlyConfigured, self.default_currency_cmd)

    @override_settings()
    def test_missing_APP_ID_update(self):
        "No APP_ID - updatecurrencies"
        from django.conf import settings
        from django.core.exceptions import ImproperlyConfigured
        del settings.OPENEXCHANGERATES_APP_ID
        self.assertRaises(ImproperlyConfigured, self.default_rate_cmd)

    @patch('requests.Session', mock_requestsession_getexception())
    def test_no_connectivity_currencies(self):
        "Simulate connection problem - currencies"
        from currencies.management.commands._openexchangerates_client import OpenExchangeRatesClientException
        self.assertRaises(OpenExchangeRatesClientException, self.default_currency_cmd)

    @patch('requests.Session', mock_requestsession_getexception())
    def test_no_connectivity_update(self):
        "Simulate connection problem - updatecurrencies"
        from currencies.management.commands._openexchangerates_client import OpenExchangeRatesClientException
        self.assertRaises(OpenExchangeRatesClientException, self.default_rate_cmd)

class OXRTest(DefaultTest):
    "Test Openexchangerates support: when specified"
    source_arg = ['oxr']


class YahooTest(ExcRatesMixin, BaseTestMixin, TestCase):
    "Test Yahoo support"
    fixtures = ['currencies_test']
    source_arg = ['yahoo']

    @patch('currencies.management.commands._yahoofinance.get', mock_requestget_exception())
    def test_no_connectivity(self):
        "Simulate connection problem - imports from cache"
        self.test_import_single_currency_short()

    @BaseTestMixin._move_cache_file('currencies.management.commands._yahoofinance')
    def test_no_cache(self):
        "Simulate no cache file - API withdrawn so will raise exception"
        self.assertRaises(RuntimeError, self.test_import_single_currency_short)

    @BaseTestMixin._move_cache_file('currencies.management.commands._yahoofinance')
    @patch('currencies.management.commands._yahoofinance.get', mock_requestget_exception())
    def test_no_connectivity_or_cache(self):
        "Simulate connection problem & no cache - exception"
        self.assertRaises(RuntimeError, self.test_import_single_currency_short)


class ISOTest(ExcRatesMixin, BaseTestMixin, TestCase):
    "Test Currency ISO support"
    fixtures = ['currencies_test']
    source_arg = ['iso']

    @patch('currencies.management.commands._currencyiso.get', mock_requestget_exception())
    def test_no_connectivity(self):
        "Simulate connection problem - imports from cache"
        self.test_import_single_currency_short()

    @BaseTestMixin._move_cache_file('currencies.management.commands._currencyiso')
    def test_no_cache(self):
        "Simulate no cache file - imports from API"
        self.test_import_single_currency_short()

    @BaseTestMixin._move_cache_file('currencies.management.commands._currencyiso')
    @patch('currencies.management.commands._currencyiso.get', mock_requestget_exception())
    def test_no_connectivity_or_cache(self):
        "Simulate connection problem & no cache - exception"
        self.assertRaises(RuntimeError, self.test_import_single_currency_short)

