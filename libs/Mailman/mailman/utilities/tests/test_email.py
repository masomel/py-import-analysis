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

"""Testing functions in the email utilities."""

import unittest

from mailman.interfaces.messages import IMessageStore
from mailman.testing.helpers import (
    specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from mailman.utilities.email import add_message_hash, split_email
from zope.component import getUtility


class TestEmail(unittest.TestCase):
    """Testing functions in the email utilities."""

    def test_normal_split(self):
        self.assertEqual(split_email('anne@example.com'),
                         ('anne', ['example', 'com']))
        self.assertEqual(split_email('anne@foo.example.com'),
                         ('anne', ['foo', 'example', 'com']))

    def test_no_at_split(self):
        self.assertEqual(split_email('anne'), ('anne', None))

    def test_adding_the_message_hash(self):
        # When the message has a Message-ID header, this will add the
        # X-Mailman-Hash-ID header.
        msg = mfs("""\
Message-ID: <aardvark>

""")
        add_message_hash(msg)
        self.assertEqual(msg['message-id-hash'],
                         '75E2XSUXAFQGWANWEROVQ7JGYMNWHJBT')

    def test_remove_hash_headers_first(self):
        # Any existing X-Mailman-Hash-ID header is removed first.
        msg = mfs("""\
Message-ID: <aardvark>
Message-ID-Hash: abc

""")
        add_message_hash(msg)
        headers = msg.get_all('message-id-hash')
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0], '75E2XSUXAFQGWANWEROVQ7JGYMNWHJBT')

    def test_hash_header_left_alone_if_no_message_id(self):
        # If the original message has no Message-ID header, then any existing
        # Message-ID-Hash headers are left intact.
        msg = mfs("""\
Message-ID-Hash: abc

""")
        add_message_hash(msg)
        headers = msg.get_all('message-id-hash')
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers[0], 'abc')

    def test_angle_brackets_dont_contribute_to_hash(self):
        # According to RFC 5322, the [matching] angle brackets do not
        # contribute to the hash.
        msg = mfs("""\
Message-ID: aardvark

""")
        add_message_hash(msg)
        self.assertEqual(msg['message-id-hash'],
                         '75E2XSUXAFQGWANWEROVQ7JGYMNWHJBT')

    def test_mismatched_angle_brackets_do_contribute_to_hash(self):
        # According to RFC 5322, the [matching] angle brackets do not
        # contribute to the hash.
        msg = mfs("""\
Message-ID: <aardvark

""")
        add_message_hash(msg)
        self.assertEqual(msg['message-id-hash'],
                         'AOJ545GHRYD2Y3RUFG2EWMPHUABTG4SM')
        msg = mfs("""\
Message-ID: aardvark>

""")
        add_message_hash(msg)
        self.assertEqual(msg['message-id-hash'],
                         '5KH3RA7ZM4VM6XOZXA7AST2XN2X4S3WY')

    def test_return_value(self):
        msg = mfs("""\
Message-ID: aardvark>

""")
        hash32 = add_message_hash(msg)
        self.assertEqual(hash32, '5KH3RA7ZM4VM6XOZXA7AST2XN2X4S3WY')


class TestMessageIDHash(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._store = getUtility(IMessageStore)

    def test_message_id_hash_backward_compatibility(self):
        msg = mfs("""\
Message-ID: <ant>

""")
        self._store.add(msg)
        stored_msg = self._store.get_message_by_id('<ant>')
        self.assertEqual(stored_msg['message-id-hash'],
                         'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')
        # For backward compatibility with the old spec.
        self.assertEqual(stored_msg['x-message-id-hash'],
                         'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')

    def test_message_id_hash_gets_replaced_backward_compatibility(self):
        msg = mfs("""\
Message-ID: <ant>
Message-ID-Hash: abc
X-Message-ID-Hash: abc

""")
        self._store.add(msg)
        stored_msg = self._store.get_message_by_id('<ant>')
        message_id_hashes = stored_msg.get_all('message-id-hash')
        self.assertEqual(len(message_id_hashes), 1)
        self.assertEqual(message_id_hashes[0],
                         'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')
        # For backward compatibility with the old spec.
        x_message_id_hashes = stored_msg.get_all('x-message-id-hash')
        self.assertEqual(len(x_message_id_hashes), 1)
        self.assertEqual(x_message_id_hashes[0],
                         'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')
