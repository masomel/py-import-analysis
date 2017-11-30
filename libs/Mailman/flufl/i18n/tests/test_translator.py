"""Tests for the Translator class.

This cannot be a doctest because of the sys._getframe() manipulations.  That
does not play well with the way doctest executes Python code.  But see
translator.txt for a description of how this should work in real Python code.
"""

import unittest

from flufl.i18n._translator import Translator


# Some globals for following tests.
purple = 'porpoises'
magenta = 'monkeys'
green = 'gerbil'


class Catalog:
    """Test catalog."""

    def __init__(self):
        self.translation = None

    def gettext(self, original):
        """Return the translation."""
        return self.translation

    def charset(self):
        """Return the encoding."""
        # The default is ascii.
        return None


class TestTranslator(unittest.TestCase):
    """Tests of the Translator class."""

    def setUp(self):
        self.catalog = Catalog()
        # We need depth=1 because we're calling the translation at the same
        # level as the locals we care about.
        self.translator = Translator(self.catalog, depth=1)

    def test_locals(self):
        # Test that locals get properly substituted.
        aqua = 'aardvarks'                          # noqa: F841
        blue = 'badgers'                            # noqa: F841
        cyan = 'cats'                               # noqa: F841
        self.catalog.translation = '$blue and $cyan and $aqua'
        self.assertEqual(self.translator.translate('source string'),
                         'badgers and cats and aardvarks')

    def test_globals(self):
        # Test that globals get properly substituted.
        self.catalog.translation = '$purple and $magenta and $green'
        self.assertEqual(self.translator.translate('source string'),
                         'porpoises and monkeys and gerbil')

    def test_dict_overrides_locals(self):
        # Test that explicit mappings override locals.
        aqua = 'aardvarks'                          # noqa: F841
        blue = 'badgers'                            # noqa: F841
        cyan = 'cats'                               # noqa: F841
        overrides = dict(blue='bats')
        self.catalog.translation = '$blue and $cyan and $aqua'
        self.assertEqual(self.translator.translate('source string', overrides),
                         'bats and cats and aardvarks')

    def test_globals_with_overrides(self):
        # Test that globals with overrides get properly substituted.
        self.catalog.translation = '$purple and $magenta and $green'
        overrides = dict(green='giraffe')
        self.assertEqual(self.translator.translate('source string', overrides),
                         'porpoises and monkeys and giraffe')

    def test_empty_string(self):
        # The empty string is always translated as the empty string.
        self.assertEqual(self.translator.translate(''), '')

    def test_dedent(self):
        # By default, the translated string is always dedented.
        aqua = 'aardvarks'                          # noqa: F841
        blue = 'badgers'                            # noqa: F841
        cyan = 'cats'                               # noqa: F841
        self.catalog.translation = """\
        These are the $blue
        These are the $cyan
        These are the $aqua
        """
        for line in self.translator.translate('source string').splitlines():
            self.assertTrue(line[:5], 'These')

    def test_no_dedent(self):
        # You can optionally suppress the dedent.
        aqua = 'aardvarks'                          # noqa: F841
        blue = 'badgers'                            # noqa: F841
        cyan = 'cats'                               # noqa: F841
        self.catalog.translation = """\
        These are the $blue
        These are the $cyan
        These are the $aqua
        """
        translator = Translator(self.catalog, dedent=False)
        for line in translator.translate('source string').splitlines():
            self.assertTrue(line[:9], '    These')
