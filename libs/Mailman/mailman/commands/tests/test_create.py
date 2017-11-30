# Copyright (C) 2011-2017 by the Free Software Foundation, Inc.
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

"""Test the `mailman create` subcommand."""

import sys
import unittest

from argparse import ArgumentParser
from contextlib import suppress
from mailman.app.lifecycle import create_list
from mailman.commands.cli_lists import Create
from mailman.testing.layers import ConfigLayer


class FakeArgs:
    language = None
    owners = []
    quiet = False
    domain = None
    listname = None
    notify = False


class FakeParser:
    def __init__(self):
        self.message = None

    def error(self, message):
        self.message = message
        sys.exit(1)


class TestCreate(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self.command = Create()
        self.command.parser = FakeParser()
        self.args = FakeArgs()

    def test_cannot_create_duplicate_list(self):
        # Cannot create a mailing list if it already exists.
        create_list('test@example.com')
        self.args.listname = ['test@example.com']
        with suppress(SystemExit):
            self.command.process(self.args)
        self.assertEqual(self.command.parser.message,
                         'List already exists: test@example.com')

    def test_invalid_posting_address(self):
        # Cannot create a mailing list with an invalid posting address.
        self.args.listname = ['foo']
        with suppress(SystemExit):
            self.command.process(self.args)
        self.assertEqual(self.command.parser.message,
                         'Illegal list name: foo')

    def test_invalid_owner_addresses(self):
        # Cannot create a list with invalid owner addresses.  LP: #778687
        self.args.listname = ['test@example.com']
        self.args.owners = ['main=True']
        with suppress(SystemExit):
            self.command.process(self.args)
        self.assertEqual(self.command.parser.message,
                         'Illegal owner addresses: main=True')

    def test_without_domain_option(self):
        # The domain will be created if no domain options are specified.
        parser = ArgumentParser()
        self.command.add(FakeParser(), parser)
        args = parser.parse_args('test@example.org'.split())
        self.assertTrue(args.domain)

    def test_with_domain_option(self):
        # The domain will be created if -d is given explicitly.
        parser = ArgumentParser()
        self.command.add(FakeParser(), parser)
        args = parser.parse_args('-d test@example.org'.split())
        self.assertTrue(args.domain)

    def test_with_nodomain_option(self):
        # The domain will not be created if --no-domain is given.
        parser = ArgumentParser()
        self.command.add(FakeParser(), parser)
        args = parser.parse_args('-D test@example.net'.split())
        self.assertFalse(args.domain)

    def test_error_when_not_creating_domain(self):
        self.args.domain = False
        self.args.listname = ['test@example.org']
        with self.assertRaises(SystemExit) as cm:
            self.command.process(self.args)
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(self.command.parser.message,
                         'Undefined domain: example.org')
