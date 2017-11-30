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

"""Test Bans and the ban manager."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.interfaces.bans import IBanManager
from mailman.interfaces.listmanager import IListManager
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestMailingListBans(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._manager = IBanManager(self._mlist)

    def test_delete_list(self):
        # All list bans must be deleted when the list is deleted.
        self._manager.ban('anne@example.com')
        getUtility(IListManager).delete(self._mlist)
        self.assertEqual(list(self._manager), [])

    def test_delete_list_does_not_delete_global_bans(self):
        # Global bans are not deleted when the list is deleted.
        global_ban_manager = IBanManager(None)
        global_ban_manager.ban('bart@example.com')
        getUtility(IListManager).delete(self._mlist)
        self.assertEqual([ban.email for ban in global_ban_manager],
                         ['bart@example.com'])

    def test_bans_sequence(self):
        # Bans returns a pageable sorted sequence.
        self._manager.ban('bee@example.com')
        self._manager.ban('ant@example.com')
        self._manager.ban('cat@example.com')
        # The results can be len()'d.
        count = len(self._manager.bans)
        self.assertEqual(count, 3)
        # The results can be iterated.
        self.assertEqual(
            ['ant@example.com', 'bee@example.com', 'cat@example.com'],
            [ban.email for ban in self._manager.bans])
        # The results can be indexed.
        self.assertEqual(
            [self._manager.bans[i].email for i in range(count)],
            ['ant@example.com', 'bee@example.com', 'cat@example.com'])
