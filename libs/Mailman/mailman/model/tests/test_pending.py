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

"""Test pendings."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.interfaces.pending import IPendable, IPendings
from mailman.model.pending import PendedKeyValue
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility
from zope.interface import implementer


@implementer(IPendable)
class SimplePendable(dict):
    PEND_TYPE = 'simple'


class TestPendings(unittest.TestCase):
    """Test pendings."""

    layer = ConfigLayer

    def test_delete_key_values(self):
        # Deleting a pending should delete its key-values.
        pendingdb = getUtility(IPendings)
        subscription = SimplePendable(
            type='subscription',
            address='aperson@example.com',
            display_name='Anne Person',
            language='en',
            password='xyz')
        token = pendingdb.add(subscription)
        self.assertEqual(pendingdb.count, 1)
        pendingdb.confirm(token)
        self.assertEqual(pendingdb.count, 0)
        self.assertEqual(config.db.store.query(PendedKeyValue).count(), 0)

    def test_find(self):
        # Test getting pendables for a mailing-list.
        mlist = create_list('list1@example.com')
        pendingdb = getUtility(IPendings)
        subscription_1 = SimplePendable(
            type='subscription',
            list_id='list1.example.com')
        subscription_2 = SimplePendable(
            type='subscription',
            list_id='list2.example.com')
        subscription_3 = SimplePendable(
            type='hold request',
            list_id='list1.example.com')
        subscription_4 = SimplePendable(
            type='hold request',
            list_id='list2.example.com')
        token_1 = pendingdb.add(subscription_1)
        pendingdb.add(subscription_2)
        token_3 = pendingdb.add(subscription_3)
        token_4 = pendingdb.add(subscription_4)
        self.assertEqual(pendingdb.count, 4)
        # Find the pending subscription in list1.
        pendings = list(pendingdb.find(mlist=mlist, pend_type='subscription'))
        self.assertEqual(len(pendings), 1)
        self.assertEqual(pendings[0][0], token_1)
        self.assertEqual(pendings[0][1]['list_id'], 'list1.example.com')
        # Find all pending hold requests.
        pendings = list(pendingdb.find(pend_type='hold request'))
        self.assertEqual(len(pendings), 2)
        self.assertSetEqual(
            set((p[0], p[1]['list_id']) for p in pendings),
            {(token_3, 'list1.example.com'), (token_4, 'list2.example.com')}
            )
        # Find all pendings for list1.
        pendings = list(pendingdb.find(mlist=mlist))
        self.assertEqual(len(pendings), 2)
        self.assertSetEqual(
            set((p[0], p[1]['list_id'], p[1]['type']) for p in pendings),
            {(token_1, 'list1.example.com', 'subscription'),
             (token_3, 'list1.example.com', 'hold request')}
            )
