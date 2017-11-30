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

"""Testing app.inject functions."""

import unittest

from mailman.app.inject import inject_message, inject_text
from mailman.app.lifecycle import create_list
from mailman.email.message import Message
from mailman.testing.helpers import (
    get_queue_messages,
    specialized_message_from_string as message_from_string)
from mailman.testing.layers import ConfigLayer


NL = '\n'


class TestInjectMessage(unittest.TestCase):
    """Test message injection."""

    layer = ConfigLayer

    def setUp(self):
        self.mlist = create_list('test@example.com')
        self.msg = message_from_string("""\
From: anne@example.com
To: test@example.com
Subject: A test message
Message-ID: <first>
Date: Tue, 14 Jun 2011 21:12:00 -0400

Nothing.
""")
        # Let assertMultiLineEqual work without bounds.

    def test_inject_message(self):
        # Test basic inject_message() call.
        inject_message(self.mlist, self.msg)
        items = get_queue_messages('in', expected_count=1)
        self.assertMultiLineEqual(items[0].msg.as_string(),
                                  self.msg.as_string())
        self.assertEqual(items[0].msgdata['listid'], 'test.example.com')
        self.assertEqual(items[0].msgdata['original_size'],
                         len(self.msg.as_string()))

    def test_inject_message_with_recipients(self):
        # Explicit recipients end up in the metadata.
        recipients = ['bart@example.com', 'cris@example.com']
        inject_message(self.mlist, self.msg, recipients)
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msgdata['recipients'], recipients)

    def test_inject_message_to_queue(self):
        # Explicitly use a different queue.
        inject_message(self.mlist, self.msg, switchboard='virgin')
        get_queue_messages('in', expected_count=0)
        items = get_queue_messages('virgin', expected_count=1)
        self.assertMultiLineEqual(items[0].msg.as_string(),
                                  self.msg.as_string())
        self.assertEqual(items[0].msgdata['listid'], 'test.example.com')
        self.assertEqual(items[0].msgdata['original_size'],
                         len(self.msg.as_string()))

    def test_inject_message_without_message_id(self):
        # inject_message() adds a Message-ID header if it's missing.
        del self.msg['message-id']
        self.assertNotIn('message-id', self.msg)
        inject_message(self.mlist, self.msg)
        self.assertIn('message-id', self.msg)
        items = get_queue_messages('in', expected_count=1)
        self.assertIn('message-id', items[0].msg)
        self.assertEqual(items[0].msg['message-id'], self.msg['message-id'])

    def test_inject_message_without_date(self):
        # inject_message() adds a Date header if it's missing.
        del self.msg['date']
        self.assertNotIn('date', self.msg)
        inject_message(self.mlist, self.msg)
        self.assertIn('date', self.msg)
        items = get_queue_messages('in', expected_count=1)
        self.assertIn('date', items[0].msg)
        self.assertEqual(items[0].msg['date'], self.msg['date'])

    def test_inject_message_with_keywords(self):
        # Keyword arguments are copied into the metadata.
        inject_message(self.mlist, self.msg, foo='yes', bar='no')
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msgdata['foo'], 'yes')
        self.assertEqual(items[0].msgdata['bar'], 'no')

    def test_inject_message_id_hash(self):
        # When the injected message has a Message-ID header, the injected
        # message will also get an Message-ID-Hash header.
        inject_message(self.mlist, self.msg)
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msg['message-id-hash'],
                         '4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB')

    def test_inject_message_id_hash_without_message_id(self):
        # When the injected message does not have a Message-ID header, a
        # Message-ID header will be added, and the injected message will also
        # get an Message-ID-Hash header.
        del self.msg['message-id']
        self.assertNotIn('message-id', self.msg)
        self.assertNotIn('message-id-hash', self.msg)
        inject_message(self.mlist, self.msg)
        items = get_queue_messages('in', expected_count=1)
        self.assertIn('message-id', items[0].msg)
        self.assertIn('message-id-hash', items[0].msg)


class TestInjectText(unittest.TestCase):
    """Test text injection."""

    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        self.mlist = create_list('test@example.com')
        self.text = """\
From: bart@example.com
To: test@example.com
Subject: A test message
Message-ID: <second>
Date: Tue, 14 Jun 2011 21:12:00 -0400

Nothing.
"""

    def _remove_line(self, header):
        return NL.join(line for line in self.text.splitlines()
                       if not line.lower().startswith(header))

    def test_inject_text(self):
        # Test basic inject_text() call.
        inject_text(self.mlist, self.text)
        items = get_queue_messages('in', expected_count=1)
        self.assertIsInstance(items[0].msg, Message)
        self.assertEqual(items[0].msg['message-id-hash'],
                         'GUXXQKNCHBFQAHGBFMGCME6HKZCUUH3K')
        # Delete these headers because they don't exist in the original text.
        del items[0].msg['message-id-hash']
        del items[0].msg['x-message-id-hash']
        self.assertMultiLineEqual(items[0].msg.as_string(), self.text)
        self.assertEqual(items[0].msgdata['listid'], 'test.example.com')
        self.assertEqual(items[0].msgdata['original_size'],
                         # Add back the Message-ID-Hash and X-Message-ID-Hash
                         # headers which wer in the message contributing to the
                         # original_size, but weren't in the original text.
                         # Don't forget the space, delimeter, and newline!
                         len(self.text) + 50 + 52)

    def test_inject_text_with_recipients(self):
        # Explicit recipients end up in the metadata.
        recipients = ['bart@example.com', 'cris@example.com']
        inject_text(self.mlist, self.text, recipients)
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msgdata['recipients'], recipients)

    def test_inject_text_to_queue(self):
        # Explicitly use a different queue.
        inject_text(self.mlist, self.text, switchboard='virgin')
        get_queue_messages('in', expected_count=0)
        items = get_queue_messages('virgin', expected_count=1)
        # Remove the Message-ID-Hash header which isn't in the original text.
        del items[0].msg['message-id-hash']
        del items[0].msg['x-message-id-hash']
        self.assertMultiLineEqual(items[0].msg.as_string(), self.text)
        self.assertEqual(items[0].msgdata['listid'], 'test.example.com')
        self.assertEqual(items[0].msgdata['original_size'],
                         # Add back the Message-ID-Hash and X-Message-ID-Hash
                         # headers which wer in the message contributing to the
                         # original_size, but weren't in the original text.
                         # Don't forget the space, delimeter, and newline!
                         len(self.text) + 50 + 52)

    def test_inject_text_without_message_id(self):
        # inject_text() adds a Message-ID header if it's missing.
        filtered = self._remove_line('message-id')
        self.assertNotIn('Message-ID', filtered)
        inject_text(self.mlist, filtered)
        items = get_queue_messages('in', expected_count=1)
        self.assertIn('message-id', items[0].msg)

    def test_inject_text_without_date(self):
        # inject_text() adds a Date header if it's missing.
        filtered = self._remove_line('date')
        self.assertNotIn('date', filtered)
        inject_text(self.mlist, self.text)
        items = get_queue_messages('in', expected_count=1)
        self.assertIn('date', items[0].msg)

    def test_inject_text_adds_original_size(self):
        # The metadata gets an original_size attribute that is the length of
        # the injected text.
        inject_text(self.mlist, self.text)
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msgdata['original_size'],
                         # Add back the Message-ID-Hash and X-Message-ID-Hash
                         # headers which wer in the message contributing to the
                         # original_size, but weren't in the original text.
                         # Don't forget the space, delimeter, and newline!
                         len(self.text) + 50 + 52)

    def test_inject_text_with_keywords(self):
        # Keyword arguments are copied into the metadata.
        inject_text(self.mlist, self.text, foo='yes', bar='no')
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msgdata['foo'], 'yes')
        self.assertEqual(items[0].msgdata['bar'], 'no')

    def test_inject_message_id_hash(self):
        # When the injected message has a Message-ID header, the injected
        # message will also get an Message-ID-Hash header.
        inject_text(self.mlist, self.text)
        items = get_queue_messages('in', expected_count=1)
        self.assertEqual(items[0].msg['message-id-hash'],
                         'GUXXQKNCHBFQAHGBFMGCME6HKZCUUH3K')

    def test_inject_message_id_hash_without_message_id(self):
        # When the injected message does not have a Message-ID header, a
        # Message-ID header will be added, and the injected message will also
        # get an Message-ID-Hash header.
        filtered = self._remove_line('message-id')
        self.assertNotIn('Message-ID', filtered)
        self.assertNotIn('Message-ID-Hash', filtered)
        inject_text(self.mlist, filtered)
        items = get_queue_messages('in', expected_count=1)
        self.assertIn('message-id', items[0].msg)
        self.assertIn('message-id-hash', items[0].msg)
