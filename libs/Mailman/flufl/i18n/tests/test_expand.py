"""Test for expand() coverage."""

import unittest

from flufl.i18n._expand import expand
from unittest.mock import patch


class FailingTemplateClass:
    def __init__(self, template):
        self.template = template

    def safe_substitute(self, *args, **kws):
        raise TypeError


class TestExpand(unittest.TestCase):
    def test_exception(self):
        with patch('flufl.i18n._expand.log.exception') as log:
            expand('my-template', {}, FailingTemplateClass)
        log.assert_called_once_with('broken template: %s', 'my-template')
