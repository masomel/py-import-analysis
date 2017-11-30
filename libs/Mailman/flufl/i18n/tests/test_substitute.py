"""Test for substitute.py coverage."""

import unittest

from flufl.i18n._substitute import attrdict
from types import SimpleNamespace


class TestSubstitute(unittest.TestCase):
    def test_attrdict_parts(self):
        ant = dict(bee=SimpleNamespace(cat=SimpleNamespace(dog='elk')))
        anteater = attrdict(ant)
        self.assertEqual(anteater['bee.cat.dog'], 'elk')

    def test_attrdict_missing(self):
        ant = dict(bee=SimpleNamespace(cat=SimpleNamespace(dog='elk')))
        anteater = attrdict(ant)
        with self.assertRaises(KeyError) as cm:
            anteater['bee.cat.doo']
        self.assertEqual(str(cm.exception), "'bee.cat.doo'")
