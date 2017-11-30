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

"""Test the to_digest handler."""

import os
import unittest

from mailman.app.lifecycle import create_list
from mailman.handlers.to_digest import ToDigest
from mailman.testing.helpers import specialized_message_from_string as mfs
from mailman.testing.layers import ConfigLayer


class TestToDigest(unittest.TestCase):
    """Test the to_digest handler."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A disposable message
Message-ID: <ant>

""")
        self._handler = ToDigest()

    def test_unicode_message(self):
        # LP: #1170347 - The message has non-ascii characters in its payload,
        # but no charset (encoding) is defined e.g. in a Content-Type header.
        self._msg.set_payload(b'non-ascii chars \xc3\xa9 \xc3\xa8 \xc3\xa7')
        self._msg['X-Test'] = 'dummy'
        self._handler.process(self._mlist, self._msg, {})
        # Make sure the digest mbox is not empty.
        mailbox_path = os.path.join(self._mlist.data_path, 'digest.mmdf')
        self.assertGreater(os.path.getsize(mailbox_path), 0)
