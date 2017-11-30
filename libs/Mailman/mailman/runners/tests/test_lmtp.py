# Copyright (C) 2012-2017 by the Free Software Foundation, Inc.
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

"""Tests for the LMTP server."""

import os
import smtplib
import unittest

from datetime import datetime
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.database.transaction import transaction
from mailman.testing.helpers import get_lmtp_client, get_queue_messages
from mailman.testing.layers import LMTPLayer


class TestLMTP(unittest.TestCase):
    """Test various aspects of the LMTP server."""

    layer = LMTPLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('test@example.com')
        self._lmtp = get_lmtp_client(quiet=True)
        self._lmtp.lhlo('remote.example.org')
        self.addCleanup(self._lmtp.close)

    def test_message_id_required(self):
        # The message is rejected if it does not have a Message-ID header.
        with self.assertRaises(smtplib.SMTPDataError) as cm:
            self._lmtp.sendmail('anne@example.com', ['test@example.com'], """\
From: anne@example.com
To: test@example.com
Subject: This has no Message-ID header

""")
        # LMTP returns a 550: Requested action not taken: mailbox unavailable
        # (e.g., mailbox not found, no access, or command rejected for policy
        # reasons)
        self.assertEqual(cm.exception.smtp_code, 550)
        self.assertEqual(cm.exception.smtp_error,
                         b'No Message-ID header provided')

    def test_message_id_hash_is_added(self):
        self._lmtp.sendmail('anne@example.com', ['test@example.com'], """\
From: anne@example.com
To: test@example.com
Message-ID: <ant>
Subject: This has a Message-ID but no Message-ID-Hash

""")
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msg['message-id-hash'],
                         'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')

    def test_original_message_id_hash_is_overwritten(self):
        self._lmtp.sendmail('anne@example.com', ['test@example.com'], """\
From: anne@example.com
To: test@example.com
Message-ID: <ant>
Message-ID-Hash: IGNOREME
Subject: This has a Message-ID but no Message-ID-Hash

""")
        items = get_queue_messages('in', expected_count=1)
        all_headers = items[0].msg.get_all('message-id-hash')
        self.assertEqual(len(all_headers), 1)
        self.assertEqual(items[0].msg['message-id-hash'],
                         'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')

    def test_received_time(self):
        # The LMTP runner adds a `received_time` key to the metadata.
        self._lmtp.sendmail('anne@example.com', ['test@example.com'], """\
From: anne@example.com
To: test@example.com
Subject: This has no Message-ID header
Message-ID: <ant>

""")
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msgdata['received_time'],
                         datetime(2005, 8, 1, 7, 49, 23))

    def test_queue_directory(self):
        # The LMTP runner is not queue runner, so it should not have a
        # directory in var/queue.
        queue_directory = os.path.join(config.QUEUE_DIR, 'lmtp')
        self.assertFalse(os.path.isdir(queue_directory))

    def test_nonexistent_mailing_list(self):
        # Trying to post to a nonexistent mailing list is an error.
        with self.assertRaises(smtplib.SMTPDataError) as cm:
            self._lmtp.sendmail('anne@example.com',
                                ['notalist@example.com'], """\
From: anne.person@example.com
To: notalist@example.com
Subject: An interesting message
Message-ID: <aardvark>

""")
        self.assertEqual(cm.exception.smtp_code, 550)
        self.assertEqual(cm.exception.smtp_error,
                         b'Requested action not taken: mailbox unavailable')

    def test_missing_subaddress(self):
        # Trying to send a message to a bogus subaddress is an error.
        with self.assertRaises(smtplib.SMTPDataError) as cm:
            self._lmtp.sendmail('anne@example.com',
                                ['test-bogus@example.com'], """\
From: anne.person@example.com
To: test-bogus@example.com
Subject: An interesting message
Message-ID: <aardvark>

""")
        self.assertEqual(cm.exception.smtp_code, 550)
        self.assertEqual(cm.exception.smtp_error,
                         b'Requested action not taken: mailbox unavailable')

    def test_mailing_list_with_subaddress(self):
        # A mailing list with a subaddress in its name should be recognized as
        # the mailing list, not as a command.
        with transaction():
            create_list('test-join@example.com')
        self._lmtp.sendmail('anne@example.com', ['test-join@example.com'], """\
From: anne@example.com
To: test-join@example.com
Message-ID: <ant>
Subject: This should not be recognized as a join command

""")
        # The message is in the incoming queue but not the command queue.
        get_queue_messages('in', expected_count=1)
        get_queue_messages('command', expected_count=0)

    def test_mailing_list_with_subaddress_command(self):
        # Like above, but we can still send a command to the mailing list.
        with transaction():
            create_list('test-join@example.com')
        self._lmtp.sendmail('anne@example.com',
                            ['test-join-join@example.com'], """\
From: anne@example.com
To: test-join-join@example.com
Message-ID: <ant>
Subject: This will be recognized as a join command.

""")
        # The message is in the command queue but not the incoming queue.
        get_queue_messages('in', expected_count=0)
        get_queue_messages('command', expected_count=1)


class TestBugs(unittest.TestCase):
    """Test some LMTP related bugs."""

    layer = LMTPLayer

    def setUp(self):
        self._lmtp = get_lmtp_client(quiet=True)
        self._lmtp.lhlo('remote.example.org')

    def test_lp1117176(self):
        # Upper cased list names can't be sent to via LMTP.
        with transaction():
            create_list('my-LIST@example.com')
        self._lmtp.sendmail('anne@example.com', ['my-list@example.com'], """\
From: anne@example.com
To: my-list@example.com
Subject: My subject
Message-ID: <alpha>

""")
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msgdata['listid'],
                         'my-list.example.com')

    def test_issue140(self):
        # Non-UTF-8 data sent to the LMTP server crashes it.
        with transaction():
            create_list('ant@example.com')
        self._lmtp.sendmail('anne@example.com', ['ant@example.com'], b"""\
From: anne@example.com
To: ant@example.com
Subject: My subject
Message-ID: <alpha>

\xa0
""")
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msg['message-id'], '<alpha>')
