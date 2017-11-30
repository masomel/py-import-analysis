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

"""Test the send-digests subcommand."""

import os
import unittest

from datetime import timedelta
from io import StringIO
from mailman.app.lifecycle import create_list
from mailman.commands.cli_digests import Digests
from mailman.config import config
from mailman.interfaces.digests import DigestFrequency
from mailman.interfaces.member import DeliveryMode
from mailman.runners.digest import DigestRunner
from mailman.testing.helpers import (
    get_queue_messages, make_testable_runner,
    specialized_message_from_string as mfs, subscribe)
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import now as right_now
from unittest.mock import patch


class FakeArgs:
    def __init__(self):
        self.lists = []
        self.send = False
        self.bump = False
        self.dry_run = False
        self.verbose = False


class TestSendDigests(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._mlist.digests_enabled = True
        self._mlist.digest_size_threshold = 100000
        self._mlist.send_welcome_message = False
        self._command = Digests()
        self._handler = config.handlers['to-digest']
        self._runner = make_testable_runner(DigestRunner, 'digest')
        # The mailing list needs at least one digest recipient.
        member = subscribe(self._mlist, 'Anne')
        member.preferences.delivery_mode = DeliveryMode.plaintext_digests

    def test_send_one_digest_by_list_id(self):
        msg = mfs("""\
To: ant@example.com
From: anne@example.com
Subject: message 1

""")
        self._handler.process(self._mlist, msg, {})
        del msg['subject']
        msg['subject'] = 'message 2'
        self._handler.process(self._mlist, msg, {})
        # There are no digests already being sent, but the ant mailing list
        # does have a digest mbox collecting messages.
        get_queue_messages('digest', expected_count=0)
        mailbox_path = os.path.join(self._mlist.data_path, 'digest.mmdf')
        self.assertGreater(os.path.getsize(mailbox_path), 0)
        args = FakeArgs()
        args.send = True
        args.lists.append('ant.example.com')
        self._command.process(args)
        self._runner.run()
        # Now, there's no digest mbox and there's a plaintext digest in the
        # outgoing queue.
        self.assertFalse(os.path.exists(mailbox_path))
        items = get_queue_messages('virgin', expected_count=1)
        digest_contents = str(items[0].msg)
        self.assertIn('Subject: message 1', digest_contents)
        self.assertIn('Subject: message 2', digest_contents)

    def test_send_one_digest_by_fqdn_listname(self):
        msg = mfs("""\
To: ant@example.com
From: anne@example.com
Subject: message 1

""")
        self._handler.process(self._mlist, msg, {})
        del msg['subject']
        msg['subject'] = 'message 2'
        self._handler.process(self._mlist, msg, {})
        # There are no digests already being sent, but the ant mailing list
        # does have a digest mbox collecting messages.
        get_queue_messages('digest', expected_count=0)
        mailbox_path = os.path.join(self._mlist.data_path, 'digest.mmdf')
        self.assertGreater(os.path.getsize(mailbox_path), 0)
        args = FakeArgs()
        args.send = True
        args.lists.append('ant@example.com')
        self._command.process(args)
        self._runner.run()
        # Now, there's no digest mbox and there's a plaintext digest in the
        # outgoing queue.
        self.assertFalse(os.path.exists(mailbox_path))
        items = get_queue_messages('virgin', expected_count=1)
        digest_contents = str(items[0].msg)
        self.assertIn('Subject: message 1', digest_contents)
        self.assertIn('Subject: message 2', digest_contents)

    def test_send_one_digest_to_missing_list_id(self):
        msg = mfs("""\
To: ant@example.com
From: anne@example.com
Subject: message 1

""")
        self._handler.process(self._mlist, msg, {})
        del msg['subject']
        msg['subject'] = 'message 2'
        self._handler.process(self._mlist, msg, {})
        # There are no digests already being sent, but the ant mailing list
        # does have a digest mbox collecting messages.
        get_queue_messages('digest', expected_count=0)
        mailbox_path = os.path.join(self._mlist.data_path, 'digest.mmdf')
        self.assertGreater(os.path.getsize(mailbox_path), 0)
        args = FakeArgs()
        args.send = True
        args.lists.append('bee.example.com')
        stderr = StringIO()
        with patch('mailman.commands.cli_digests.sys.stderr', stderr):
            self._command.process(args)
        self._runner.run()
        # The warning was printed to stderr.
        self.assertEqual(stderr.getvalue(),
                         'No such list found: bee.example.com\n')
        # And no digest was prepared.
        self.assertGreater(os.path.getsize(mailbox_path), 0)
        get_queue_messages('virgin', expected_count=0)

    def test_send_one_digest_to_missing_fqdn_listname(self):
        msg = mfs("""\
To: ant@example.com
From: anne@example.com
Subject: message 1

""")
        self._handler.process(self._mlist, msg, {})
        del msg['subject']
        msg['subject'] = 'message 2'
        self._handler.process(self._mlist, msg, {})
        # There are no digests already being sent, but the ant mailing list
        # does have a digest mbox collecting messages.
        get_queue_messages('digest', expected_count=0)
        mailbox_path = os.path.join(self._mlist.data_path, 'digest.mmdf')
        self.assertGreater(os.path.getsize(mailbox_path), 0)
        args = FakeArgs()
        args.send = True
        args.lists.append('bee@example.com')
        stderr = StringIO()
        with patch('mailman.commands.cli_digests.sys.stderr', stderr):
            self._command.process(args)
        self._runner.run()
        # The warning was printed to stderr.
        self.assertEqual(stderr.getvalue(),
                         'No such list found: bee@example.com\n')
        # And no digest was prepared.
        self.assertGreater(os.path.getsize(mailbox_path), 0)
        get_queue_messages('virgin', expected_count=0)

    def test_send_digest_to_one_missing_and_one_existing_list(self):
        msg = mfs("""\
To: ant@example.com
From: anne@example.com
Subject: message 1

""")
        self._handler.process(self._mlist, msg, {})
        del msg['subject']
        msg['subject'] = 'message 2'
        self._handler.process(self._mlist, msg, {})
        # There are no digests already being sent, but the ant mailing list
        # does have a digest mbox collecting messages.
        get_queue_messages('digest', expected_count=0)
        mailbox_path = os.path.join(self._mlist.data_path, 'digest.mmdf')
        self.assertGreater(os.path.getsize(mailbox_path), 0)
        args = FakeArgs()
        args.send = True
        args.lists.extend(('ant.example.com', 'bee.example.com'))
        stderr = StringIO()
        with patch('mailman.commands.cli_digests.sys.stderr', stderr):
            self._command.process(args)
        self._runner.run()
        # The warning was printed to stderr.
        self.assertEqual(stderr.getvalue(),
                         'No such list found: bee.example.com\n')
        # But ant's digest was still prepared.
        self.assertFalse(os.path.exists(mailbox_path))
        items = get_queue_messages('virgin', expected_count=1)
        digest_contents = str(items[0].msg)
        self.assertIn('Subject: message 1', digest_contents)
        self.assertIn('Subject: message 2', digest_contents)

    def test_send_digests_for_two_lists(self):
        # Populate ant's digest.
        msg = mfs("""\
To: ant@example.com
From: anne@example.com
Subject: message 1

""")
        self._handler.process(self._mlist, msg, {})
        del msg['subject']
        msg['subject'] = 'message 2'
        self._handler.process(self._mlist, msg, {})
        # Create the second list.
        bee = create_list('bee@example.com')
        bee.digests_enabled = True
        bee.digest_size_threshold = 100000
        bee.send_welcome_message = False
        member = subscribe(bee, 'Bart')
        member.preferences.delivery_mode = DeliveryMode.plaintext_digests
        # Populate bee's digest.
        msg = mfs("""\
To: bee@example.com
From: bart@example.com
Subject: message 3

""")
        self._handler.process(bee, msg, {})
        del msg['subject']
        msg['subject'] = 'message 4'
        self._handler.process(bee, msg, {})
        # There are no digests for either list already being sent, but the
        # mailing lists do have a digest mbox collecting messages.
        ant_mailbox_path = os.path.join(self._mlist.data_path, 'digest.mmdf')
        self.assertGreater(os.path.getsize(ant_mailbox_path), 0)
        # Check bee's digest.
        bee_mailbox_path = os.path.join(bee.data_path, 'digest.mmdf')
        self.assertGreater(os.path.getsize(bee_mailbox_path), 0)
        # Both.
        get_queue_messages('digest', expected_count=0)
        # Process both list's digests.
        args = FakeArgs()
        args.send = True
        args.lists.extend(('ant.example.com', 'bee@example.com'))
        self._command.process(args)
        self._runner.run()
        # Now, neither list has a digest mbox and but there are plaintext
        # digest in the outgoing queue for both.
        self.assertFalse(os.path.exists(ant_mailbox_path))
        self.assertFalse(os.path.exists(bee_mailbox_path))
        items = get_queue_messages('virgin', expected_count=2)
        # Figure out which digest is going to ant and which to bee.
        if items[0].msg['to'] == 'ant@example.com':
            ant = items[0].msg
            bee = items[1].msg
        else:
            assert items[0].msg['to'] == 'bee@example.com'
            ant = items[1].msg
            bee = items[0].msg
        # Check ant's digest.
        digest_contents = str(ant)
        self.assertIn('Subject: message 1', digest_contents)
        self.assertIn('Subject: message 2', digest_contents)
        # Check bee's digest.
        digest_contents = str(bee)
        self.assertIn('Subject: message 3', digest_contents)
        self.assertIn('Subject: message 4', digest_contents)

    def test_send_digests_for_all_lists(self):
        # Populate ant's digest.
        msg = mfs("""\
To: ant@example.com
From: anne@example.com
Subject: message 1

""")
        self._handler.process(self._mlist, msg, {})
        del msg['subject']
        msg['subject'] = 'message 2'
        self._handler.process(self._mlist, msg, {})
        # Create the second list.
        bee = create_list('bee@example.com')
        bee.digests_enabled = True
        bee.digest_size_threshold = 100000
        bee.send_welcome_message = False
        member = subscribe(bee, 'Bart')
        member.preferences.delivery_mode = DeliveryMode.plaintext_digests
        # Populate bee's digest.
        msg = mfs("""\
To: bee@example.com
From: bart@example.com
Subject: message 3

""")
        self._handler.process(bee, msg, {})
        del msg['subject']
        msg['subject'] = 'message 4'
        self._handler.process(bee, msg, {})
        # There are no digests for either list already being sent, but the
        # mailing lists do have a digest mbox collecting messages.
        ant_mailbox_path = os.path.join(self._mlist.data_path, 'digest.mmdf')
        self.assertGreater(os.path.getsize(ant_mailbox_path), 0)
        # Check bee's digest.
        bee_mailbox_path = os.path.join(bee.data_path, 'digest.mmdf')
        self.assertGreater(os.path.getsize(bee_mailbox_path), 0)
        # Both.
        get_queue_messages('digest', expected_count=0)
        # Process all mailing list digests by not setting any arguments.
        args = FakeArgs()
        args.send = True
        self._command.process(args)
        self._runner.run()
        # Now, neither list has a digest mbox and but there are plaintext
        # digest in the outgoing queue for both.
        self.assertFalse(os.path.exists(ant_mailbox_path))
        self.assertFalse(os.path.exists(bee_mailbox_path))
        items = get_queue_messages('virgin', expected_count=2)
        # Figure out which digest is going to ant and which to bee.
        if items[0].msg['to'] == 'ant@example.com':
            ant = items[0].msg
            bee = items[1].msg
        else:
            assert items[0].msg['to'] == 'bee@example.com'
            ant = items[1].msg
            bee = items[0].msg
        # Check ant's digest.
        digest_contents = str(ant)
        self.assertIn('Subject: message 1', digest_contents)
        self.assertIn('Subject: message 2', digest_contents)
        # Check bee's digest.
        digest_contents = str(bee)
        self.assertIn('Subject: message 3', digest_contents)
        self.assertIn('Subject: message 4', digest_contents)

    def test_send_no_digest_ready(self):
        # If no messages have been sent through the mailing list, no digest
        # can be sent.
        mailbox_path = os.path.join(self._mlist.data_path, 'digest.mmdf')
        self.assertFalse(os.path.exists(mailbox_path))
        args = FakeArgs()
        args.send = True
        args.lists.append('ant.example.com')
        self._command.process(args)
        self._runner.run()
        get_queue_messages('virgin', expected_count=0)

    def test_bump_before_send(self):
        self._mlist.digest_volume_frequency = DigestFrequency.monthly
        self._mlist.volume = 7
        self._mlist.next_digest_number = 4
        self._mlist.digest_last_sent_at = right_now() + timedelta(
            days=-32)
        msg = mfs("""\
To: ant@example.com
From: anne@example.com
Subject: message 1

""")
        self._handler.process(self._mlist, msg, {})
        args = FakeArgs()
        args.bump = True
        args.send = True
        args.lists.append('ant.example.com')
        self._command.process(args)
        self._runner.run()
        # The volume is 8 and the digest number is 2 because a digest was sent
        # after the volume/number was bumped.
        self.assertEqual(self._mlist.volume, 8)
        self.assertEqual(self._mlist.next_digest_number, 2)
        self.assertEqual(self._mlist.digest_last_sent_at, right_now())
        items = get_queue_messages('virgin', expected_count=1)
        self.assertEqual(items[0].msg['subject'], 'Ant Digest, Vol 8, Issue 1')


class TestBumpVolume(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._mlist.digest_volume_frequency = DigestFrequency.monthly
        self._mlist.volume = 7
        self._mlist.next_digest_number = 4
        self.right_now = right_now()
        self._command = Digests()

    def test_bump_one_list(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            days=-32)
        args = FakeArgs()
        args.bump = True
        args.lists.append('ant.example.com')
        self._command.process(args)
        self.assertEqual(self._mlist.volume, 8)
        self.assertEqual(self._mlist.next_digest_number, 1)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_two_lists(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            days=-32)
        # Create the second list.
        bee = create_list('bee@example.com')
        bee.digest_volume_frequency = DigestFrequency.monthly
        bee.volume = 7
        bee.next_digest_number = 4
        bee.digest_last_sent_at = self.right_now + timedelta(
            days=-32)
        args = FakeArgs()
        args.bump = True
        args.lists.extend(('ant.example.com', 'bee.example.com'))
        self._command.process(args)
        self.assertEqual(self._mlist.volume, 8)
        self.assertEqual(self._mlist.next_digest_number, 1)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_verbose(self):
        args = FakeArgs()
        args.bump = True
        args.verbose = True
        args.lists.append('ant.example.com')
        output = StringIO()
        with patch('sys.stdout', output):
            self._command.process(args)
        self.assertMultiLineEqual(output.getvalue(), """\
ant.example.com is at volume 7, number 4
ant.example.com bumped to volume 7, number 5
""")

    def test_send_verbose(self):
        args = FakeArgs()
        args.send = True
        args.verbose = True
        args.dry_run = True
        args.lists.append('ant.example.com')
        output = StringIO()
        with patch('sys.stdout', output):
            self._command.process(args)
        self.assertMultiLineEqual(output.getvalue(), """\
ant.example.com sent volume 7, number 4
""")
