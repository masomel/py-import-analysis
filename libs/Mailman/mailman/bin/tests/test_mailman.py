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

"""Test mailman command utilities."""

import unittest

from contextlib import ExitStack
from datetime import timedelta
from io import StringIO
from mailman.app.lifecycle import create_list
from mailman.bin.mailman import main
from mailman.config import config
from mailman.database.transaction import transaction
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import now
from unittest.mock import patch


class TestMailmanCommand(unittest.TestCase):
    layer = ConfigLayer

    def test_mailman_command_without_subcommand_prints_help(self):
        # Issue #137: Running `mailman` without a subcommand raises an
        # AttributeError.
        testargs = ['mailman']
        output = StringIO()
        with patch('sys.argv', testargs), patch('sys.stdout', output):
            with self.assertRaises(SystemExit):
                main()
        self.assertIn('usage', output.getvalue())

    def test_transaction_commit_after_successful_subcommand(self):
        # Issue #223: Subcommands which change the database need to commit or
        # abort the transaction.
        with transaction():
            mlist = create_list('ant@example.com')
            mlist.volume = 5
            mlist.next_digest_number = 3
            mlist.digest_last_sent_at = now() - timedelta(days=60)
        testargs = ['mailman', 'digests', '-b', '-l', 'ant@example.com']
        output = StringIO()
        with ExitStack() as resources:
            enter = resources.enter_context
            enter(patch('sys.argv', testargs))
            enter(patch('sys.stdout', output))
            # Everything is already initialized.
            enter(patch('mailman.bin.mailman.initialize'))
            main()
        # Clear the current transaction to force a database reload.
        config.db.abort()
        self.assertEqual(mlist.volume, 6)
        self.assertEqual(mlist.next_digest_number, 1)

    def test_transaction_abort_after_failing_subcommand(self):
        with transaction():
            mlist = create_list('ant@example.com')
            mlist.volume = 5
            mlist.next_digest_number = 3
            mlist.digest_last_sent_at = now() - timedelta(days=60)
        testargs = ['mailman', 'digests', '-b', '-l', 'ant@example.com',
                    '--send']
        output = StringIO()
        with ExitStack() as resources:
            enter = resources.enter_context
            enter(patch('sys.argv', testargs))
            enter(patch('sys.stdout', output))
            # Force an exception in the subcommand.
            enter(patch('mailman.commands.cli_digests.maybe_send_digest_now',
                        side_effect=RuntimeError))
            # Everything is already initialized.
            enter(patch('mailman.bin.mailman.initialize'))
            with self.assertRaises(RuntimeError):
                main()
        # Clear the current transaction to force a database reload.
        config.db.abort()
        # The volume and number haven't changed.
        self.assertEqual(mlist.volume, 5)
        self.assertEqual(mlist.next_digest_number, 3)
