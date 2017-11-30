# Copyright (C) 2013-2017 by the Free Software Foundation, Inc.
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

"""Test the conf subcommand."""

import os
import sys
import tempfile
import unittest

from io import StringIO
from mailman.commands.cli_conf import Conf
from mailman.testing.layers import ConfigLayer
from unittest import mock


class FakeArgs:
    section = None
    key = None
    output = None
    sort = False


class FakeParser:
    def __init__(self):
        self.message = None

    def error(self, message):
        self.message = message
        sys.exit(1)


class TestConf(unittest.TestCase):
    """Test the conf subcommand."""

    layer = ConfigLayer

    def setUp(self):
        self.command = Conf()
        self.command.parser = FakeParser()
        self.args = FakeArgs()

    def test_cannot_access_nonexistent_section(self):
        self.args.section = 'thissectiondoesnotexist'
        self.args.key = None
        with self.assertRaises(SystemExit):
            self.command.process(self.args)
        self.assertEqual(self.command.parser.message,
                         'No such section: thissectiondoesnotexist')

    def test_cannot_access_nonexistent_key(self):
        self.args.section = "mailman"
        self.args.key = 'thiskeydoesnotexist'
        with self.assertRaises(SystemExit):
            self.command.process(self.args)
        self.assertEqual(self.command.parser.message,
                         'Section mailman: No such key: thiskeydoesnotexist')

    def test_output_to_explicit_stdout(self):
        self.args.output = '-'
        self.args.section = 'shell'
        self.args.key = 'use_ipython'
        with mock.patch('sys.stdout') as mock_object:
            self.command.process(self.args)
        mock_object.write.assert_has_calls(
            [mock.call('no'), mock.call('\n')])

    def test_output_to_file(self):
        self.args.section = 'shell'
        self.args.key = 'use_ipython'
        fd, filename = tempfile.mkstemp()
        try:
            self.args.output = filename
            self.command.process(self.args)
            with open(filename, 'r') as fp:
                contents = fp.read()
        finally:
            os.remove(filename)
        self.assertEqual(contents, 'no\n')

    def test_sort_by_section(self):
        self.args.output = '-'
        self.args.sort = True
        output = StringIO()
        with mock.patch('sys.stdout', output):
            self.command.process(self.args)
        last_line = ''
        for line in output.getvalue().splitlines():
            if not line.startswith('['):
                # This is a continuation line.  --sort doesn't sort these.
                continue
            self.assertTrue(line > last_line,
                            '{} !> {}'.format(line, last_line))
            last_line = line
