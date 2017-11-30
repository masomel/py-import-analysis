# Copyright (C) 2016-2017 by the Free Software Foundation, Inc.
#
# This file is part of GNU Mailman.
#
# GNU Mailman is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# GNU Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# GNU Mailman.  If not, see <http://www.gnu.org/licenses/>.

"""Test the interact utility."""


import sys
import unittest

from contextlib import ExitStack
from io import StringIO
from mailman.app.lifecycle import create_list
from mailman.testing.helpers import hackenv
from mailman.testing.layers import ConfigLayer
from mailman.utilities.interact import interact
from tempfile import NamedTemporaryFile
from unittest.mock import patch


class TestInteract(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        resources = ExitStack()
        self.addCleanup(resources.close)
        self._enter = resources.enter_context
        self._enter(patch('builtins.input', side_effect=EOFError))
        self._stderr = StringIO()
        self._enter(patch('sys.stderr', self._stderr))

    def test_interact(self):
        mlist = create_list('ant@example.com')
        results = []
        fp = self._enter(NamedTemporaryFile('w', encoding='utf-8'))
        self._enter(hackenv('PYTHONSTARTUP', fp.name))
        print('results.append(mlist.list_id)', file=fp)
        fp.flush()
        interact()
        self.assertEqual(results, [mlist.list_id])

    def test_interact_overrides(self):
        create_list('ant@example.com')
        bee = create_list('bee@example.com')
        results = []
        fp = self._enter(NamedTemporaryFile('w', encoding='utf-8'))
        self._enter(hackenv('PYTHONSTARTUP', fp.name))
        print('results.append(mlist.list_id)', file=fp)
        fp.flush()
        interact(overrides=dict(mlist=bee))
        self.assertEqual(results, [bee.list_id])

    def test_interact_default_banner(self):
        self._enter(hackenv('PYTHONSTARTUP', None))
        interact()
        stderr = self._stderr.getvalue().splitlines()
        banner = 'Python {} on {} '.format(sys.version, sys.platform)
        self.assertEqual(stderr[0], banner.splitlines()[0])

    def test_interact_custom_banner(self):
        self._enter(hackenv('PYTHONSTARTUP', None))
        interact(banner='Welcome')
        stderr = self._stderr.getvalue().splitlines()
        self.assertEqual(stderr[0], 'Welcome')

    def test_interact_no_upframe(self):
        upframed = False                                         # noqa: F841
        fp = self._enter(NamedTemporaryFile('w', encoding='utf-8'))
        self._enter(hackenv('PYTHONSTARTUP', fp.name))
        print('print(upframed)', file=fp)
        fp.flush()
        interact(upframe=False, banner='')
        lines = self._stderr.getvalue().splitlines()
        self.assertIn("NameError: name 'upframed' is not defined", lines)

    def test_interact_multiline(self):
        # GL issue #224.
        fp = self._enter(NamedTemporaryFile('w', encoding='utf-8'))
        self._enter(hackenv('PYTHONSTARTUP', fp.name))
        print('import sys', file=fp)
        print("print('hello', file=sys.stderr)", file=fp)
        print("print('world', file=sys.stderr)", file=fp)
        fp.flush()
        interact(banner='')
        lines = self._stderr.getvalue()
        self.assertEqual(lines, 'hello\nworld\n\n', lines)
