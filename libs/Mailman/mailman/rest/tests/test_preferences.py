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

"""Test various preference functionality."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.database.transaction import transaction
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import call_api
from mailman.testing.layers import RESTLayer
from urllib.error import HTTPError
from zope.component import getUtility


class TestPreferences(unittest.TestCase):
    """Test various preference functionality."""

    layer = RESTLayer

    def setUp(self):
        user_manager = getUtility(IUserManager)
        with transaction():
            self._mlist = create_list('test@example.com')
            anne = user_manager.create_address('anne@example.com')
            self._member = self._mlist.subscribe(anne)

    def test_read_only_member_all_preferences(self):
        # A member's combined preferences are read-only.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/members/1/all/preferences', {
                     'delivery_status': 'enabled',
                     }, method='PATCH')
        # The resource at this endpoint doesn't even have a PATCH method.
        self.assertEqual(cm.exception.code, 405)

    def test_read_only_system_preferences(self):
        # The system preferences are read-only.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/system/preferences', {
                     'delivery_status': 'enabled',
                     }, method='PATCH')
        # The resource at this endpoint doesn't even have a PATCH method.
        self.assertEqual(cm.exception.code, 405)
