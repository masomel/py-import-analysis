# Copyright (C) 2011-2017 by the Free Software Foundation, Inc.
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

"""Test the UID model class."""

import uuid
import unittest

from mailman.config import config
from mailman.interfaces.usermanager import IUserManager
from mailman.model.uid import UID
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestUID(unittest.TestCase):
    layer = ConfigLayer

    def test_record(self):
        # Test that the .record() method works.
        UID.record(uuid.UUID(int=11))
        UID.record(uuid.UUID(int=99))
        self.assertRaises(ValueError, UID.record, uuid.UUID(int=11))

    def test_longs(self):
        # In a non-test environment, the uuid will be a long int.
        my_uuid = uuid.uuid4()
        UID.record(my_uuid)
        self.assertRaises(ValueError, UID.record, my_uuid)

    def test_get_total_uid_count(self):
        # The reserved REST API needs this.
        for i in range(10):
            UID.record(uuid.uuid4())
        self.assertEqual(UID.get_total_uid_count(), 10)

    def test_cull_orphan_uids(self):
        # The reserved REST API needs to cull entries from the uid table that
        # are not associated with actual entries in the user table.
        manager = getUtility(IUserManager)
        uids = set()
        for i in range(10):
            user = manager.create_user()
            uids.add(user.user_id)
            # The testing infrastructure does not record the UIDs for new user
            # objects, so do that now to mimic the real system.
            UID.record(user.user_id)
        self.assertEqual(len(uids), 10)
        # Now add some orphan uids.
        orphans = set()
        for i in range(100, 113):
            uid = UID.record(uuid.UUID(int=i))
            orphans.add(uid.uid)
        self.assertEqual(len(orphans), 13)
        # Normally we wouldn't do a query in a test, since we'd want the model
        # object to expose this, but we actually don't support exposing all
        # the UIDs to the rest of Mailman.
        all_uids = set(row[0] for row in config.db.store.query(UID.uid))
        self.assertEqual(all_uids, uids | orphans)
        # Now, cull all the UIDs that aren't associated with users.  Do use
        # the model API for this.
        UID.cull_orphans()
        non_orphans = set(row[0] for row in config.db.store.query(UID.uid))
        self.assertEqual(uids, non_orphans)
        # And all the users still exist.
        non_orphans = set(user.user_id for user in manager.users)
        self.assertEqual(uids, non_orphans)

    def test_repr(self):
        uid = UID(uuid.UUID(int=1))
        self.assertTrue(repr(uid).startswith(
            '<UID 00000000-0000-0000-0000-000000000001 at '))
        self.assertTrue(repr(uid).endswith('>'))
