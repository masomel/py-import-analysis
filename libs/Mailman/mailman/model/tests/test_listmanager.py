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

"""Test the ListManager."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.app.moderator import hold_message
from mailman.config import config
from mailman.interfaces.address import InvalidEmailAddressError
from mailman.interfaces.autorespond import IAutoResponseSet, Response
from mailman.interfaces.domain import IDomainManager
from mailman.interfaces.listmanager import (
    IListManager, ListAlreadyExistsError, ListCreatedEvent, ListCreatingEvent,
    ListDeletedEvent, ListDeletingEvent)
from mailman.interfaces.mailinglist import IListArchiverSet
from mailman.interfaces.messages import IMessageStore
from mailman.interfaces.pending import IPendable, IPendings
from mailman.interfaces.requests import IListRequests
from mailman.interfaces.subscriptions import ISubscriptionService
from mailman.interfaces.usermanager import IUserManager
from mailman.model.mime import ContentFilter
from mailman.testing.helpers import (
    event_subscribers, specialized_message_from_string)
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility
from zope.interface import implementer


@implementer(IPendable)
class SimplePendable(dict):
    PEND_TYPE = 'simple'


class TestListManager(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._events = []

    def _record_event(self, event):
        self._events.append(event)

    def test_create_list_event(self):
        # Test that creating a list in the list manager propagates the
        # expected events.
        with event_subscribers(self._record_event):
            mlist = getUtility(IListManager).create('test@example.com')
        self.assertEqual(len(self._events), 2)
        self.assertIsInstance(self._events[0], ListCreatingEvent)
        self.assertEqual(self._events[0].fqdn_listname, 'test@example.com')
        self.assertIsInstance(self._events[1], ListCreatedEvent)
        self.assertEqual(self._events[1].mailing_list, mlist)

    def test_delete_list_event(self):
        # Test that deleting a list in the list manager propagates the
        # expected event.
        mlist = create_list('another@example.com')
        with event_subscribers(self._record_event):
            getUtility(IListManager).delete(mlist)
        self.assertEqual(len(self._events), 2)
        self.assertIsInstance(self._events[0], ListDeletingEvent)
        self.assertEqual(self._events[0].mailing_list, mlist)
        self.assertIsInstance(self._events[1], ListDeletedEvent)
        self.assertEqual(self._events[1].fqdn_listname, 'another@example.com')

    def test_list_manager_list_ids(self):
        # You can get all the list ids for all the existing mailing lists.
        create_list('ant@example.com')
        create_list('bee@example.com')
        create_list('cat@example.com')
        self.assertEqual(
            sorted(getUtility(IListManager).list_ids),
            ['ant.example.com', 'bee.example.com', 'cat.example.com'])

    def test_delete_list_with_list_archiver_set(self):
        # Ensure that mailing lists with archiver sets can be deleted.  In
        # issue #115, this fails under PostgreSQL, but not SQLite.
        mlist = create_list('ant@example.com')
        # We don't keep a reference to this archiver set just because it makes
        # pyflakes unhappy.  It doesn't change the outcome.
        IListArchiverSet(mlist)
        list_manager = getUtility(IListManager)
        list_manager.delete(mlist)
        self.assertIsNone(list_manager.get('ant@example.com'))

    def test_delete_list_with_autoresponse_record(self):
        # Ensure that mailing lists with auto-response sets can be deleted.  In
        # issue #115, this fails under PostgreSQL, but not SQLite.
        list_manager = getUtility(IListManager)
        user_manager = getUtility(IUserManager)
        mlist = create_list('ant@example.com')
        address = user_manager.create_address('aperson@example.com')
        autoresponse_set = IAutoResponseSet(mlist)
        autoresponse_set.response_sent(address, Response.hold)
        list_manager.delete(mlist)
        self.assertIsNone(list_manager.get('ant@example.com'))

    def test_find_advertised_lists(self):
        ant = create_list('ant@example.com')
        bee = create_list('bee@example.com')
        self.assertTrue(bee.advertised)
        ant.advertised = False
        result = getUtility(IListManager).find(advertised=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], bee)

    def test_find_by_mail_host_and_advertised(self):
        ant = create_list('ant@example.com')
        bee = create_list('bee@example.com')
        getUtility(IDomainManager).add('example.org')
        cat = create_list('cat@example.org')
        dog = create_list('dog@example.org')
        self.assertTrue(bee.advertised)
        ant.advertised = False
        self.assertTrue(cat.advertised)
        dog.advertised = False
        result = getUtility(IListManager).find(
            mail_host='example.org', advertised=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], cat)


class TestListLifecycleEvents(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._ant = create_list('ant@example.com')
        self._bee = create_list('bee@example.com')
        self._usermanager = getUtility(IUserManager)

    def test_members_are_deleted_when_mailing_list_is_deleted(self):
        # When a mailing list with members is deleted, all the Member records
        # are also deleted.
        anne = self._usermanager.create_address('anne@example.com')
        bart = self._usermanager.create_address('bart@example.com')
        anne_ant = self._ant.subscribe(anne)
        anne_bee = self._bee.subscribe(anne)
        bart_ant = self._ant.subscribe(bart)
        anne_ant_id = anne_ant.member_id
        anne_bee_id = anne_bee.member_id
        bart_ant_id = bart_ant.member_id
        getUtility(IListManager).delete(self._ant)
        service = getUtility(ISubscriptionService)
        # We deleted the ant@example.com mailing list.  Anne's and Bart's
        # membership in this list should now be removed, but Anne's membership
        # in bee@example.com should still exist.
        self.assertIsNone(service.get_member(anne_ant_id))
        self.assertIsNone(service.get_member(bart_ant_id))
        self.assertEqual(service.get_member(anne_bee_id), anne_bee)

    def test_requests_are_deleted_when_mailing_list_is_deleted(self):
        # When a mailing list is deleted, its requests database is deleted
        # too, e.g. all its message hold requests (but not the messages
        # themselves).
        msg = specialized_message_from_string("""\
From: anne@example.com
To: ant@example.com
Subject: Hold me
Message-ID: <argon>

""")
        request_id = hold_message(self._ant, msg)
        getUtility(IListManager).delete(self._ant)
        # This is a hack.  ListRequests don't access self._mailinglist in
        # their get_request() method.
        requestsdb = IListRequests(self._bee)
        request = requestsdb.get_request(request_id)
        self.assertEqual(request, None)
        saved_message = getUtility(IMessageStore).get_message_by_id('<argon>')
        self.assertEqual(saved_message.as_string(), msg.as_string())

    def test_content_filters_are_deleted_when_mailing_list_is_deleted(self):
        # When a mailing list with content filters is deleted, the filters
        # must be deleted first or an IntegrityError will be raised.
        filter_names = ('filter_types', 'pass_types',
                        'filter_extensions', 'pass_extensions')
        for name in filter_names:
            setattr(self._ant, name, ['test-filter-1', 'test-filter-2'])
        getUtility(IListManager).delete(self._ant)
        filters = config.db.store.query(ContentFilter).filter_by(
            mailing_list=self._ant)
        self.assertEqual(filters.count(), 0)

    def test_pendings_are_deleted_when_mailing_list_is_deleted(self):
        pendingdb = getUtility(IPendings)
        pendable_1 = SimplePendable(
            type='subscription',
            list_id='ant.example.com')
        pendingdb.add(pendable_1)
        pendable_2 = SimplePendable(
            type='subscription',
            list_id='bee.example.com')
        pendingdb.add(pendable_2)
        self.assertEqual(pendingdb.count, 2)
        list_manager = getUtility(IListManager)
        list_manager.delete(self._ant)
        self.assertEqual(pendingdb.count, 1)
        list_manager.delete(self._bee)
        self.assertEqual(pendingdb.count, 0)


class TestListCreation(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._manager = getUtility(IListManager)

    def test_create_list_case_folding(self):
        # LP: #1117176 describes a problem where list names created in upper
        # case are not actually usable by the LMTP server.  MySQL
        # automatically changes the case of the arguments so this test will
        # always fail in case of MySQL.
        self._manager.create('my-LIST@example.com')
        self.assertIsNone(self._manager.get('my-LIST@example.com'))
        mlist = self._manager.get('my-list@example.com')
        self.assertEqual(mlist.list_id, 'my-list.example.com')

    def test_cannot_create_a_list_twice(self):
        self._manager.create('ant@example.com')
        self.assertRaises(ListAlreadyExistsError,
                          self._manager.create, 'ant@example.com')

    def test_list_name_must_be_fully_qualified(self):
        with self.assertRaises(InvalidEmailAddressError) as cm:
            self._manager.create('foo')
        self.assertEqual(cm.exception.email, 'foo')
