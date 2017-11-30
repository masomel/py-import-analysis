# Copyright (C) 2016-2017 by the Free Software Foundation, Inc.
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

"""Test the `suspicious` rule."""


import unittest

from email.header import Header
from mailman.app.lifecycle import create_list
from mailman.email.message import Message
from mailman.rules import suspicious
from mailman.testing.layers import ConfigLayer


class TestSuspicious(unittest.TestCase):
    """Test the suspicious rule."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._rule = suspicious.SuspiciousHeader()

    def test_header_instance(self):
        msg = Message()
        msg['From'] = Header('user@example.com')
        self._mlist.bounce_matching_headers = 'from: spam@example.com'
        result = self._rule.check(self._mlist, msg, {})
        self.assertFalse(result)
