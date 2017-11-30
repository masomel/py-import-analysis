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

"""Test the owner chain."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.chains.owner import BuiltInOwnerChain
from mailman.core.chains import process
from mailman.interfaces.chain import AcceptOwnerEvent
from mailman.testing.helpers import (
    event_subscribers, get_queue_messages,
    specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer


class TestOwnerChain(unittest.TestCase):
    """Test the owner chain."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._msg = mfs("""\
From: anne@example.com
To: test@example.com
Message-ID: <ant>

""")

    def test_owner_pipeline(self):
        # Messages processed through the default owners chain end up in the
        # pipeline queue, and an event gets sent.
        #
        # This event subscriber records the event that occurs when the message
        # is processed by the owner chain.
        events = []
        def catch_event(event):                                  # noqa: E306
            if isinstance(event, AcceptOwnerEvent):
                events.append(event)
        with event_subscribers(catch_event):
            process(self._mlist, self._msg, {}, 'default-owner-chain')
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertIsInstance(event, AcceptOwnerEvent)
        self.assertEqual(event.mlist, self._mlist)
        self.assertEqual(event.msg['message-id'], '<ant>')
        self.assertIsInstance(event.chain, BuiltInOwnerChain)
        items = get_queue_messages('pipeline', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['message-id'], '<ant>')
