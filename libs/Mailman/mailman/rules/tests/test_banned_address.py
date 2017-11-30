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

"""Test the `banned-address` rule."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.interfaces.bans import IBanManager
from mailman.interfaces.usermanager import IUserManager
from mailman.rules import banned_address
from mailman.testing.helpers import (
    set_preferred, specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestBannedAddress(unittest.TestCase):
    """Test the banned-address rule."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')

    def test_no_banned_sender(self):
        # Simple case where the sender is not banned.
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_user('anne@example.com')
        set_preferred(anne)
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        rule = banned_address.BannedAddress()
        result = rule.check(self._mlist, msg, {})
        self.assertFalse(result)

    def test_simple_banned_sender(self):
        # Simple case where the sender is banned.
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_user('anne@example.com')
        set_preferred(anne)
        IBanManager(self._mlist).ban('anne@example.com')
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        rule = banned_address.BannedAddress()
        result = rule.check(self._mlist, msg, {})
        self.assertTrue(result)

    def test_banned_address_linked_to_user(self):
        # Anne is subscribed to a mailing list as a user with her preferred
        # address.  She also has a secondary address which is banned and which
        # she uses to post to the mailing list.  The rule matches because the
        # posting address is banned.
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_user('anne@example.com')
        set_preferred(anne)
        anne.link(user_manager.create_address('anne.person@example.com'))
        IBanManager(self._mlist).ban('anne.person@example.com')
        msg = mfs("""\
From: anne.person@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        rule = banned_address.BannedAddress()
        result = rule.check(self._mlist, msg, {})
        self.assertTrue(result)

    def test_banned_sender_among_multiple_senders(self):
        # Two addresses are created, one of which is banned.  The rule matches
        # because all senders are checked.
        user_manager = getUtility(IUserManager)
        user_manager.create_address('anne@example.com')
        user_manager.create_address('bart@example.com')
        IBanManager(self._mlist).ban('bart@example.com')
        msg = mfs("""\
From: anne@example.com
Sender: bart@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        rule = banned_address.BannedAddress()
        result = rule.check(self._mlist, msg, {})
        self.assertTrue(result)
