# Copyright (C) 2014-2017 by the Free Software Foundation, Inc.
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

"""Test the message store."""

import os
import unittest

from mailman.config import config
from mailman.interfaces.messages import IMessageStore
from mailman.model.message import Message
from mailman.testing.helpers import (
    specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from mailman.utilities.email import add_message_hash
from zope.component import getUtility


class TestMessageStore(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._store = getUtility(IMessageStore)

    def test_message_id_required(self):
        # The Message-ID header is required in order to add it to the store.
        message = mfs("""\
Subject: An important message

This message is very important.
""")
        self.assertRaises(ValueError, self._store.add, message)

    def test_get_message_by_hash(self):
        # Messages have an X-Message-ID-Hash header, the value of which can be
        # used to look the message up in the message store.
        msg = mfs("""\
Subject: An important message
Message-ID: <ant>

This message is very important.
""")
        add_message_hash(msg)
        self._store.add(msg)
        self.assertEqual(msg['x-message-id-hash'],
                         'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')
        found = self._store.get_message_by_hash(
            'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')
        self.assertEqual(found['message-id'], '<ant>')
        self.assertEqual(found['x-message-id-hash'],
                         'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')

    def test_can_delete_missing_message(self):
        # Deleting a message which isn't in the store does not raise an
        # exception.
        msg = mfs("""\
Message-ID: <ant>

""")
        self._store.add(msg)
        self.assertEqual(len(list(self._store.messages)), 1)
        self._store.delete_message('missing')
        self.assertEqual(len(list(self._store.messages)), 1)

    def test_can_survive_missing_message_path(self):
        # Deleting a message which is in the store, but which doesn't appear
        # on the file system does not raise an exception, but still removes
        # the message from the store.
        msg = mfs("""\
Message-ID: <ant>

""")
        self._store.add(msg)
        self.assertEqual(len(list(self._store.messages)), 1)
        # We have to use the SQLAlchemy API because the .get_message_by_*()
        # methods return email Message objects, not IMessages.  The former
        # does not give us the path to the object on the file system.
        row = config.db.store.query(Message).filter_by(
            message_id='<ant>').first()
        os.remove(os.path.join(config.MESSAGES_DIR, row.path))
        self._store.delete_message('<ant>')
        self.assertEqual(len(list(self._store.messages)), 0)

    def test_message_id_hash(self):
        # The new specification calls for a Message-ID-Hash header,
        # specifically without the X- prefix.
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

    def test_message_id_hash_gets_replaced(self):
        # Any existing Message-ID-Hash header (or for backward compatibility
        # X-Message-ID-Hash) gets replaced with its new value.
        msg = mfs("""\
Subject: Testing
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

    def test_add_message_duplicate_okay(self):
        msg = mfs("""\
Subject: Once
Message-ID: <ant>

""")
        hash32 = self._store.add(msg)
        stored_msg = self._store.get_message_by_id('<ant>')
        self.assertEqual(msg['subject'], stored_msg['subject'])
        self.assertEqual(msg['message-id-hash'], hash32)
        # A second insertion, even if headers change, does not store the
        # message twice.
        del msg['subject']
        msg['Subject'] = 'Twice'
        hash32 = self._store.add(msg)
        stored_msg = self._store.get_message_by_id('<ant>')
        self.assertNotEqual(msg['subject'], stored_msg['subject'])
        self.assertIsNone(hash32)
