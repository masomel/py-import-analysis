# Copyright (C) 2015-2017 by the Free Software Foundation, Inc.
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

"""Test the `mailman members` command."""

import sys
import unittest

from functools import partial
from io import StringIO
from mailman.app.lifecycle import create_list
from mailman.commands.cli_members import Members
from mailman.interfaces.member import MemberRole
from mailman.testing.helpers import subscribe
from mailman.testing.layers import ConfigLayer
from tempfile import NamedTemporaryFile
from unittest.mock import patch


class FakeArgs:
    input_filename = None
    output_filename = None
    role = None
    regular = None
    digest = None
    nomail = None
    list = None


class FakeParser:
    def __init__(self):
        self.message = None

    def error(self, message):
        self.message = message
        sys.exit(1)


class TestCLIMembers(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self.command = Members()
        self.command.parser = FakeParser()
        self.args = FakeArgs()

    def test_no_such_list(self):
        self.args.list = ['bee.example.com']
        with self.assertRaises(SystemExit):
            self.command.process(self.args)
        self.assertEqual(self.command.parser.message,
                         'No such list: bee.example.com')

    def test_bad_delivery_status(self):
        self.args.list = ['ant.example.com']
        self.args.nomail = 'bogus'
        with self.assertRaises(SystemExit):
            self.command.process(self.args)
        self.assertEqual(self.command.parser.message,
                         'Unknown delivery status: bogus')

    def test_role_administrator(self):
        subscribe(self._mlist, 'Anne', role=MemberRole.owner)
        subscribe(self._mlist, 'Bart', role=MemberRole.moderator)
        subscribe(self._mlist, 'Cate', role=MemberRole.nonmember)
        subscribe(self._mlist, 'Dave', role=MemberRole.member)
        self.args.list = ['ant.example.com']
        self.args.role = 'administrator'
        with NamedTemporaryFile('w', encoding='utf-8') as outfp:
            self.args.output_filename = outfp.name
            self.command.process(self.args)
            with open(outfp.name, 'r', encoding='utf-8') as infp:
                lines = infp.readlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], 'Anne Person <aperson@example.com>\n')
        self.assertEqual(lines[1], 'Bart Person <bperson@example.com>\n')

    def test_role_any(self):
        subscribe(self._mlist, 'Anne', role=MemberRole.owner)
        subscribe(self._mlist, 'Bart', role=MemberRole.moderator)
        subscribe(self._mlist, 'Cate', role=MemberRole.nonmember)
        subscribe(self._mlist, 'Dave', role=MemberRole.member)
        self.args.list = ['ant.example.com']
        self.args.role = 'any'
        with NamedTemporaryFile('w', encoding='utf-8') as outfp:
            self.args.output_filename = outfp.name
            self.command.process(self.args)
            with open(outfp.name, 'r', encoding='utf-8') as infp:
                lines = infp.readlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0], 'Anne Person <aperson@example.com>\n')
        self.assertEqual(lines[1], 'Bart Person <bperson@example.com>\n')
        self.assertEqual(lines[2], 'Cate Person <cperson@example.com>\n')
        self.assertEqual(lines[3], 'Dave Person <dperson@example.com>\n')

    def test_role_moderator(self):
        subscribe(self._mlist, 'Anne', role=MemberRole.owner)
        subscribe(self._mlist, 'Bart', role=MemberRole.moderator)
        subscribe(self._mlist, 'Cate', role=MemberRole.nonmember)
        subscribe(self._mlist, 'Dave', role=MemberRole.member)
        self.args.list = ['ant.example.com']
        self.args.role = 'moderator'
        with NamedTemporaryFile('w', encoding='utf-8') as outfp:
            self.args.output_filename = outfp.name
            self.command.process(self.args)
            with open(outfp.name, 'r', encoding='utf-8') as infp:
                lines = infp.readlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Bart Person <bperson@example.com>\n')

    def test_bad_role(self):
        self.args.list = ['ant.example.com']
        self.args.role = 'bogus'
        with self.assertRaises(SystemExit):
            self.command.process(self.args)
        self.assertEqual(self.command.parser.message,
                         'Unknown member role: bogus')

    def test_already_subscribed_with_display_name(self):
        subscribe(self._mlist, 'Anne')
        outfp = StringIO()
        with NamedTemporaryFile('w', buffering=1, encoding='utf-8') as infp:
            print('Anne Person <aperson@example.com>', file=infp)
            self.args.list = ['ant.example.com']
            self.args.input_filename = infp.name
            with patch('builtins.print', partial(print, file=outfp)):
                self.command.process(self.args)
        self.assertEqual(
           outfp.getvalue(),
           'Already subscribed (skipping): Anne Person <aperson@example.com>\n'
           )
