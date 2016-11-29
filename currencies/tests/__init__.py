import os

import django


# tests discovering for grand Django's
if django.VERSION < (1, 6):
    try:
        from unittest2 import TestLoader  # py{25,26}
    except ImportError:
        from unittest import TestLoader

    def suite():
        return TestLoader().discover(os.path.dirname(__file__), pattern="test_*.py")

