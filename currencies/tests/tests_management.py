# -*- coding: utf-8 -*-
"""
Various test cases for the `currencies` and `updatecurrencies` management commands
"""
from __future__ import unicode_literals
import re, os, sys
from decimal import Decimal
from datetime import datetime, timedelta
from functools import wraps
from six import StringIO

if sys.version_info.major >= 3:
    from unittest.mock import patch, MagicMock
else:
    from mock import patch, MagicMock

from django import template
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.core.exceptions import ImproperlyConfigured
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



# Mock get requests instead of hammering the API's
def mock_requestget_response(filename):
    "Returns a mock get response with the contents of a file"
    # Cache the file content to guard against reading from & writing to the same file
    with open(filename, 'rb') as fp:
        _content = fp.read()
    def mock_resp_json(*args, **kwargs):
        import json
        # Supply a default encoding for python 2.7
        return json.loads(_content.decode('utf-8'), *args, **kwargs)
    mockget = MagicMock()
    resp = mockget.return_value
    resp.raise_for_status.return_value = None
    resp.json.side_effect = mock_resp_json
    resp.content = _content
    return mockget

# Mock helper function for oxr rates support without a valid API key for testing
def mock_requestsession_getjson(filename):
    "Sets up the mock session instance to return a fixed json rates file"
    mocksess = MagicMock()
    sessInst = mocksess.return_value
    sessInst.get = mock_requestget_response(filename)
    return mocksess


# Mock request exception helpers for simulating connectivity problems
def mock_requestget_exception():
    "Sets up the mock get instance to raise a Request exception"
    from requests.exceptions import RequestException
    mockget = MagicMock()
    mockget.side_effect = RequestException('Mocked Exception')
    return mockget

def mock_requestsession_getexception():
    "Sets up the mock session instance to raise a Request exception"
    mocksess = MagicMock()
    sessInst = mocksess.return_value
    sessInst.get = mock_requestget_exception()
    return mocksess


# Mock the source APIs for the main tests for speed and to prevent hammering & DoS protection
# We don't mock yahoo because it's already down
@patch('currencies.management.commands._currencyiso.get',
    mock_requestget_response(
        os.path.join(os.path.dirname(cwd), 'management', 'commands', '_currencyiso.xml')))
@patch('currencies.management.commands._openexchangerates_client.requests.Session',
    mock_requestsession_getjson(
        os.path.join(os.path.dirname(cwd), 'management', 'commands', '_openexchangerates.json')))
class BaseTestMixin(object):
    """
    Test suite for minimal source functionality:
    Currencies - code & name
    Symbols - inherited by base handler taken from static file currencies.json
    No cache file
    No info
    No rate updates - factor
    Tests for functionality can be overridden with the included mixins
    """
    source_arg = ()

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
    _min_info = ['Created', 'Modified']

    def run_cmd_verify_stdout(self, min_lines, cmd, *args, **kwargs):
        "Runs the given command with full verbosity and checks there are output strings"
        args = self.source_arg + args
        kwargs.setdefault('verbosity', 3)
        buf = StringIO()
        call_command(cmd, stdout=buf, stderr=buf, *args, **kwargs)
        output = buf.getvalue().splitlines()
        buf.close()
        self.assertGreaterEqual(len(output), min_lines)
        return output

    def default_currency_cmd(self):
        "Single currency import that is reused for a lot of basic tests"
        return self.run_cmd_verify_stdout(2, 'currencies', '-i=' + self._code_2dp)

    def import_all(self):
        return self.run_cmd_verify_stdout(20, 'currencies')

    def import_one(self):
        return self.run_cmd_verify_stdout(2, 'currencies')

    def default_rate_cmd(self):
        "Rate update command that is reused for a lot of basic tests. Uses the base from the db"
        return self.run_cmd_verify_stdout(3, 'updatecurrencies')

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
        Django 1.11 introduced queryset difference(). This would be a better way to implement this wrapper
        but currently we're supporting 1.8
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

    def _verify_new_currencylist(currency_list):
        "Wrapper for testing a specific list of currencies"
        def decorator(func):
            @wraps(func)
            def wrapper(inst, *args, **kwargs):
                qs = Currency.objects.all()
                for code in currency_list:
                    inst.assertRaises(Currency.DoesNotExist, qs.get, code=code)
                ret = func(inst, *args, **kwargs)
                qs = Currency.objects.all()
                for code in currency_list:
                    inst.assertIs(qs.filter(code=code).exists(), True)
                return ret
            return wrapper
        return decorator

    def _verify_new_names(func):
        "Wrapper for checking new currencies get a sensible name"
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            ret = func(inst, *args, **kwargs)
            names = zip(inst._newcodes, inst._newnames)
            qs = Currency.objects.all()
            for code, name in names:
                inst.assertRegexpMatches(qs.get(code=code).name, name)
            return ret
        return wrapper

    def _verify_new_symbols(func):
        "Wrapper for checking some new symbols have been populated"
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            ret = func(inst, *args, **kwargs)
            symbs = zip(inst._newcodes, inst._newsymbs)
            qs = Currency.objects.all()
            for code, symb in symbs:
                inst.assertEqual(qs.get(code=code).symbol, symb)
            return ret
        return wrapper

    def _verify_no_info(func):
        "Wrapper for checking info is minimal on new imports"
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            ret = func(inst, *args, **kwargs)
            qs = Currency.objects.all()
            for code in inst._newcodes:
                inst.assertEqual(sorted(list(qs.get(code=code).info.keys())), inst._min_info)
            return ret
        return wrapper


    ### TESTS FOR SOURCES THAT SUPPORT IMPORTING NEW CURRENCIES ###
    ## POSITIVE Tests ##
    @_verify_new_currencies
    def test_import_all_currencies_bydefault(self):
        "Currencies: No parameters imports all currencies"
        self.import_all()

    @_verify_new_currencies
    def test_import_all_currencies_byemptysetting(self):
        "Currencies: Empty CURRENCIES setting imports all currencies"
        with self.settings(CURRENCIES=[]):
            self.import_all()

    @_verify_new_currencylist([_code_0dp])
    @_verify_new_currencies
    def test_import_variable_CURRENCIES(self):
        "Currencies: CURRENCIES setting works"
        with self.settings(CURRENCIES=[self._code_0dp]):
            self.import_one()

    @_verify_new_currencylist([_code_2dp])
    @_verify_new_currencies
    def test_import_variable_SHOP_CURRENCIES(self):
        "Currencies: SHOP_CURRENCIES setting works"
        with self.settings(SHOP_CURRENCIES=[self._code_2dp]):
            self.import_one()

    @_verify_new_currencylist([_code_0dp])
    @_verify_new_currencies
    def test_import_variable_BOTH(self):
        "Currencies: CURRENCIES setting is given priority"
        with self.settings(SHOP_CURRENCIES=[self._code_2dp], CURRENCIES=[self._code_0dp]):
            self.import_one()
        self.assertRaises(Currency.DoesNotExist, Currency.objects.get, code=self._code_2dp)

    @_verify_new_currencylist([_code_3dp])
    @_verify_new_currencies
    def test_import_variable_WIBBLE(self):
        "Currencies: Custom setting works"
        with self.settings(WIBBLE=[self._code_3dp]):
            self.run_cmd_verify_stdout(2, 'currencies', '--import=WIBBLE')

    @_verify_new_currencylist([_code_0dp])
    @_verify_new_currencies
    def test_import_single_currency_long(self):
        "Currencies: Long import syntax"
        self.run_cmd_verify_stdout(2, 'currencies', '--import=' + self._code_0dp)

    @_verify_new_currencylist([_code_2dp])
    @_verify_new_currencies
    def test_import_single_currency_short(self):
        "Currencies: Short import syntax"
        self.default_currency_cmd()

    @_verify_new_symbols
    @_verify_new_names
    @_verify_new_currencylist(_newcodes)
    @_verify_new_currencies
    def test_import_single_currencies_mix(self):
        "Currencies: Mix of import syntax. Also names and symbols are populated"
        self.run_cmd_verify_stdout(3, 'currencies',
            '--import=' + self._code_3dp, '-i=' + self._code_2dp, '-i=' + self._code_0dp)

    def test_skip_existing_currency(self):
        "Currencies: Skip existing currency"
        before = Currency.objects.get(code=self._code_exist)
        self.run_cmd_verify_stdout(2, 'currencies', '-i=' + self._code_exist)
        after = Currency.objects.get(code=self._code_exist)
        self.assertEqual(before.name, after.name)
        self.assertEqual(before.symbol, after.symbol)
        self.assertEqual(before.factor, after.factor)
        self.assertEqual(before.info, after.info)

    def test_force_existing_currency(self):
        "Currencies: Overwrite existing currency"
        before = Currency.objects.get(code=self._code_exist)
        runtime = datetime.now()
        self.run_cmd_verify_stdout(2, 'currencies', '--force', '-i=' + self._code_exist)
        after = Currency.objects.get(code=self._code_exist)
        self.assertNotEqual(before.info, after.info)
        self.assertAlmostEqual(runtime, fromisoformat(after.info['Modified']), delta=self._now_delta)

    # Test overridden in IncInfoMixin
    @_verify_no_info
    def test_info(self):
        "Currencies: only minimal info captured"
        self.import_all()

    # Test overridden in IncRatesMixin
    @_verify_stdout_msg(['source does not provide currency rate information', 'Deprecated'])
    def test_update_rates(self):
        "Rates: not supported"
        return self.default_rate_cmd()

    ## NEGATIVE Tests ##
    # This test is overridden in IncCacheMixin
    def test_no_connectivity(self):
        "Currencies: Simulate connection problem"
        with patch('currencies.management.commands._openexchangerates_client.requests.Session',
            mock_requestsession_getexception()):
            self.assertRaises(Exception, self.default_currency_cmd)

    def test_import_invalid_variable(self):
        "Currencies: Invalid import options"
        with self.assertRaises(AttributeError):
            self.run_cmd_verify_stdout(2, 'currencies', '--import=WIBBLE')
        with self.assertRaises(ImproperlyConfigured):
            self.run_cmd_verify_stdout(2, 'currencies', '-i=')
        with self.assertRaises(ImproperlyConfigured):
            self.run_cmd_verify_stdout(2, 'currencies', '-i=AB')
        with self.assertRaises(ImproperlyConfigured):
            self.run_cmd_verify_stdout(2, 'currencies', '-i=gbp')
        with self.assertRaises(ImproperlyConfigured):
            self.run_cmd_verify_stdout(2, 'currencies', '--import=ZZZ')


class IncCacheMixin(object):
    "For source handlers that cache their currencies"

    def _move_cache_file(modulename):
        "Wrapper for testing the currency cache file. Keeps the newest file with size>0"
        def decorator(func):
            @wraps(func)
            def wrapper(inst, *args, **kwargs):
                from importlib import import_module
                from random import randint
                module = import_module(modulename)
                modfile = module.CurrencyHandler._cached_currency_file
                orgfile = os.path.join(os.path.dirname(modfile), str(randint(100000, 999999)) + '.tmp')
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

    @patch('currencies.management.commands._currencyiso.CurrencyHandler.endpoint', 'http://www.google.com/test.xml')
    @patch('currencies.management.commands._yahoofinance.CurrencyHandler.endpoint', 'http://www.google.com/test.json')
    def test_import_source_down(self):
        "Currencies: Simulate source down - imports from cache"
        self.default_currency_cmd()

    @patch('currencies.management.commands._currencyiso.get', mock_requestget_exception())
    @patch('currencies.management.commands._yahoofinance.get', mock_requestget_exception())
    def test_no_connectivity(self):
        "Currencies: Simulate connection problem - imports from cache"
        self.default_currency_cmd()

    @_move_cache_file('currencies.management.commands._currencyiso')
    @_move_cache_file('currencies.management.commands._yahoofinance')
    def test_no_cache(self):
        "Currencies: Simulate no cache file - imports from API"
        self.default_currency_cmd()

    @_move_cache_file('currencies.management.commands._currencyiso')
    @_move_cache_file('currencies.management.commands._yahoofinance')
    @patch('currencies.management.commands._currencyiso.get', mock_requestget_exception())
    @patch('currencies.management.commands._yahoofinance.get', mock_requestget_exception())
    def test_no_connectivity_or_cache(self):
        "Currencies: Simulate connection problem & no cache - exception"
        self.assertRaises(RuntimeError, self.default_currency_cmd)

    # Strange fix for externally referenced python 2.7 decorator methods
    if sys.version_info.major == 2:
        _move_cache_file = staticmethod(_move_cache_file)


class IncInfoMixin(object):
    "For sources that support currency info"

    def _verify_new_info(func):
        "Wrapper for checking info is imported on new imports"
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            ret = func(inst, *args, **kwargs)
            qs = Currency.objects.all()
            for code in inst._newcodes:
                inst.assertNotEqual(sorted(list(qs.get(code=code).info.keys())), inst._min_info)
            return ret
        return wrapper

    @_verify_new_info
    def test_info(self):
        "Currencies: extra info"
        self.import_all()


@patch('currencies.management.commands._openexchangerates_client.requests.Session',
    mock_requestsession_getjson(os.path.join(cwd, 'oxr_USD.json')))
class IncRatesMixin(object):
    "For sources that support exchange rates"

    def _verify_rates(base_code):
        "Wrapper for testing that the rates are not 1.0 after an update and the specified base is set"
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

    def _verify_rate_change(func):
        "Wrapper to ensure the base changed"
        @wraps(func)
        def wrapper(inst, *args, **kwargs):
            before_base = Currency.objects.get(is_base=True).code
            ret = func(inst, *args, **kwargs)
            after_base = Currency.objects.get(is_base=True).code
            inst.assertNotEqual(before_base, after_base)
            return ret
        return wrapper

    ## POSITIVE Tests ##
    @_verify_rates('USD')
    def test_update_rates_nobase(self):
        "Rates: Update without supplying a base at all - USD"
        base = Currency.objects.update(is_base=False)
        self.default_rate_cmd()

    @_verify_rates(BaseTestMixin._code_base)
    def test_update_rates(self):
        "Rates: Update currency rates with the db base"
        self.default_rate_cmd()

    @_verify_rate_change
    @_verify_rates(BaseTestMixin._code_exist)
    def test_update_rates_specifybase(self):
        "Rates: Update currency rates with a specific base"
        self.run_cmd_verify_stdout(4, 'updatecurrencies', '--base=' + self._code_exist)

    @_verify_rate_change
    @_verify_rates(BaseTestMixin._code_exist)
    def test_update_rates_variable_CURRENCIES_BASE(self):
        "Rates: Update currency rates using the CURRENCIES_BASE setting variable"
        with self.settings(CURRENCIES_BASE=self._code_exist):
            self.default_rate_cmd()

    @_verify_rate_change
    @_verify_rates(BaseTestMixin._code_exist)
    def test_update_rates_variable_SHOP_DEFAULT_CURRENCY(self):
        "Rates: Update currency rates using the SHOP_DEFAULT_CURRENCY setting variable"
        with self.settings(SHOP_DEFAULT_CURRENCY=self._code_exist):
            self.default_rate_cmd()

    @_verify_rate_change
    @_verify_rates(BaseTestMixin._code_exist)
    def test_update_rates_variable_BOTH(self):
        "Rates: CURRENCIES_BASE is given priority"
        with self.settings(CURRENCIES_BASE=self._code_exist, SHOP_DEFAULT_CURRENCY=self._code_base):
            self.default_rate_cmd()

    @_verify_rate_change
    @_verify_rates(BaseTestMixin._code_exist)
    def test_update_rates_variable_WIBBLE(self):
        "Rates: Update currency rates using the WIBBLE setting variable"
        with self.settings(WIBBLE=self._code_exist):
            self.run_cmd_verify_stdout(4, 'updatecurrencies', '--base=WIBBLE')

    ## NEGATIVE Tests ##
    def test_update_rates_invalid_variable(self):
        "Rates: Invalid base option"
        with self.assertRaises(AttributeError):
            self.run_cmd_verify_stdout(2, 'updatecurrencies', '--base=WIBBLE')
        with self.assertRaises(ImproperlyConfigured):
            self.run_cmd_verify_stdout(2, 'updatecurrencies', '-b=' + self._code_2dp)
        with self.assertRaises(ImproperlyConfigured):
            self.run_cmd_verify_stdout(2, 'updatecurrencies', '-b=AB')
        with self.assertRaises(ImproperlyConfigured):
            self.run_cmd_verify_stdout(2, 'updatecurrencies', '-b=gbp')
        with self.assertRaises(ImproperlyConfigured):
            self.run_cmd_verify_stdout(2, 'updatecurrencies', '--base=ZZZ')

    def test_update_no_connectivity(self):
        "Rates: Simulate connection problem"
        # Patch inside the function to override the class patch
        with patch('currencies.management.commands._openexchangerates_client.requests.Session',
            mock_requestsession_getexception()):
            self.assertRaises(Exception, self.default_rate_cmd)



### ACTUAL CURRENCY SOURCE TEST CLASSES ###
@override_settings( **default_settings )
#TODO: No caching of currencies currently implemented for OpenExchangeRates: IncCacheMixin
class DefaultTest(IncRatesMixin, BaseTestMixin, TestCase):
    "Test OpenExchangeRates support: the default source"
    fixtures = ['currencies_test']

    ## NEGATIVE Tests ##
    @override_settings()
    def test_missing_APP_ID_currencies(self):
        "Currencies: No APP_ID"
        from django.conf import settings
        del settings.OPENEXCHANGERATES_APP_ID
        self.assertRaises(ImproperlyConfigured, self.default_currency_cmd)

    @override_settings()
    def test_missing_APP_ID_update(self):
        "Rates: No APP_ID"
        from django.conf import settings
        del settings.OPENEXCHANGERATES_APP_ID
        self.assertRaises(ImproperlyConfigured, self.default_rate_cmd)


class OXRTest(DefaultTest):
    "Test OpenExchangeRates support: when specified"
    source_arg = ('oxr',)


class YahooTest(IncInfoMixin, IncCacheMixin, BaseTestMixin, TestCase):
    "Test Yahoo support"
    fixtures = ['currencies_test']
    source_arg = ('yahoo',)

    ## NEGATIVE Tests ##
    # Overrides the base test due to API withdrawal
    @IncCacheMixin._move_cache_file('currencies.management.commands._yahoofinance')
    def test_no_cache(self):
        "Currencies: Simulate no cache file - API withdrawn so will raise exception"
        self.assertRaises(RuntimeError, self.default_currency_cmd)


class ISOTest(IncInfoMixin, IncCacheMixin, BaseTestMixin, TestCase):
    "Test Currency ISO support"
    fixtures = ['currencies_test']
    source_arg = ('iso',)

