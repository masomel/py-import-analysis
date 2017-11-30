import os
import doctest

from contextlib import ExitStack


DOCTEST_FLAGS = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_NDIFF)


def setup(testobj):
    """Test setup."""
    testobj.globs['cleanups'] = ExitStack()
    # Ensure that environment variables affecting translation are neutralized.
    for envar in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        if envar in os.environ:
            del os.environ[envar]


def teardown(testobj):
    testobj.globs['cleanups'].close()
