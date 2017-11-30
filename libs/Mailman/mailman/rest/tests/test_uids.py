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

"""Test deletion of orphaned UIDs.

There is no doctest for this functionality, since it's only useful for testing
of external clients of the REST API.
"""

import unittest

from mailman.config import config
from mailman.database.transaction import transaction
from mailman.interfaces.usermanager import IUserManager
from mailman.model.uid import UID
from mailman.testing.helpers import call_api
from mailman.testing.layers import RESTLayer
from zope.component import getUtility


class TestUIDs(unittest.TestCase):
    layer = RESTLayer

    def test_delete_orphans(self):
        # When users are deleted, their UIDs are generally not deleted.  We
        # never delete rows from that table in order to guarantee no
        # duplicates.  However, some external testing frameworks want to be
        # able to reset the UID table, so they can use this interface to do
        # so.  See LP: #1420083.
        #
        # Create some users.
        manager = getUtility(IUserManager)
        users_by_uid = {}
        with transaction():
            for i in range(10):
                user = manager.create_user()
                users_by_uid[user.user_id] = user
                # The testing infrastructure does not record the UIDs for new
                # user options, so do that now to mimic the real system.
                UID.record(user.user_id)
        # We now have 10 unique uids.
        self.assertEqual(len(users_by_uid), 10)
        # Now delete all the users.
        with transaction():
            for user in list(users_by_uid.values()):
                manager.delete_user(user)
        # There are still 10 unique uids in the database.
        self.assertEqual(UID.get_total_uid_count(), 10)
        # Cull the orphan UIDs.
        content, response = call_api(
            'http://localhost:9001/3.0/reserved/uids/orphans',
            method='DELETE')
        self.assertEqual(response.status_code, 204)
        # Now there are no uids in the table.
        config.db.abort()
        self.assertEqual(UID.get_total_uid_count(), 0)
