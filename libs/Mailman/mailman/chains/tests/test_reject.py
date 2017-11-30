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

"""Test the reject chain."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.core.chains import process as process_chain
from mailman.testing.helpers import (
    get_queue_messages, specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer


class TestReject(unittest.TestCase):
    """Test the reject chain."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: Ignore

""")

    def test_reject_reasons(self):
        # The bounce message must contain the moderation reasons.
        msgdata = dict(moderation_reasons=[
            'TEST-REASON-1',
            'TEST-REASON-2',
            ])
        process_chain(self._mlist, self._msg, msgdata, start_chain='reject')
        bounces = get_queue_messages('virgin', expected_count=1)
        payload = bounces[0].msg.get_payload(0).as_string()
        self.assertIn('TEST-REASON-1', payload)
        self.assertIn('TEST-REASON-2', payload)

    def test_no_reason(self):
        # There may be no moderation reasons.
        process_chain(self._mlist, self._msg, {}, start_chain='reject')
        bounces = get_queue_messages('virgin', expected_count=1)
        payload = bounces[0].msg.get_payload(0).as_string()
        self.assertIn('No bounce details are available', payload)
