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

"""Test the withlist/shell command."""

import os
import unittest

from mailman.commands.cli_withlist import Withlist
from mailman.config import config
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import configuration
from mailman.testing.layers import ConfigLayer
from unittest.mock import patch

try:
    import readline                                 # noqa: F401
    has_readline = True
except ImportError:
    has_readline = False


class FakeArgs:
    interactive = None
    run = None
    details = False
    listname = None


class TestShell(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._shell = Withlist()

    def test_namespace(self):
        args = FakeArgs()
        args.interactive = True
        with patch.object(self._shell, '_start_python') as mock:
            self._shell.process(args)
        self.assertEqual(mock.call_count, 1)
        # Don't test that all names are available, just a few choice ones.
        positional, keywords = mock.call_args
        namespace = positional[0]
        self.assertIn('getUtility', namespace)
        self.assertIn('IArchiver', namespace)
        self.assertEqual(namespace['IUserManager'], IUserManager)

    @configuration('shell', banner='my banner')
    def test_banner(self):
        args = FakeArgs()
        args.interactive = True
        with patch('mailman.commands.cli_withlist.interact') as mock:
            self._shell.process(args)
        self.assertEqual(mock.call_count, 1)
        positional, keywords = mock.call_args
        self.assertEqual(keywords['banner'], 'my banner\n')

    @unittest.skipUnless(has_readline, 'readline module is not available')
    @configuration('shell', history_file='$var_dir/history.py')
    def test_history_file(self):
        args = FakeArgs()
        args.interactive = True
        with patch('mailman.commands.cli_withlist.interact'):
            self._shell.process(args)
        history_file = os.path.join(config.VAR_DIR, 'history.py')
        self.assertTrue(os.path.exists(history_file))
