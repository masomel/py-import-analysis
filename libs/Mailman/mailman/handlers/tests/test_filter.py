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

"""Test the filter handler."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.interfaces.mime import FilterAction
from mailman.interfaces.pipeline import DiscardMessage
from mailman.testing.helpers import specialized_message_from_string as mfs
from mailman.testing.layers import ConfigLayer


class TestFilters(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')

    def test_discard_when_outer_type_matches(self):
        # When the outer MIME type of the message matches a filter type, the
        # entire message is discarded.
        self._mlist.filter_content = True
        self._mlist.filter_types = ['image/jpeg']
        self._mlist.filter_action = FilterAction.discard
        msg = mfs("""\
From: aperson@example.com
Content-Type: image/jpeg
MIME-Version: 1.0

xxxxx
""")
        self.assertRaises(DiscardMessage,
                          config.handlers['mime-delete'].process,
                          self._mlist, msg, {})
