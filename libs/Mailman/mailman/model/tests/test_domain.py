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

"""Test domains."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.interfaces.domain import (
    DomainCreatedEvent, DomainCreatingEvent, DomainDeletedEvent,
    DomainDeletingEvent, IDomainManager)
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import event_subscribers
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestDomainManager(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._events = []
        self._manager = getUtility(IDomainManager)

    def _record_event(self, event):
        self._events.append(event)

    def test_create_domain_event(self):
        # Test that creating a domain in the domain manager propagates the
        # expected events.
        with event_subscribers(self._record_event):
            domain = self._manager.add('example.org')
        self.assertEqual(len(self._events), 2)
        self.assertIsInstance(self._events[0], DomainCreatingEvent)
        self.assertEqual(self._events[0].mail_host, 'example.org')
        self.assertIsInstance(self._events[1], DomainCreatedEvent)
        self.assertEqual(self._events[1].domain, domain)

    def test_delete_domain_event(self):
        # Test that deleting a domain in the domain manager propagates the
        # expected event.
        domain = self._manager.add('example.org')
        with event_subscribers(self._record_event):
            self._manager.remove('example.org')
        self.assertEqual(len(self._events), 2)
        self.assertIsInstance(self._events[0], DomainDeletingEvent)
        self.assertEqual(self._events[0].domain, domain)
        self.assertIsInstance(self._events[1], DomainDeletedEvent)
        self.assertEqual(self._events[1].mail_host, 'example.org')

    def test_lookup_missing_domain(self):
        # Like dictionaries, getitem syntax raises KeyError on missing domain.
        with self.assertRaises(KeyError):
            self._manager['doesnotexist.com']

    def test_delete_missing_domain(self):
        # Trying to delete a missing domain gives you a KeyError.
        self.assertRaises(KeyError, self._manager.remove, 'doesnotexist.com')

    def test_domain_creation_no_default_owners(self):
        # If a domain is created without owners, then it has none.
        domain = self._manager.add('example.org')
        self.assertEqual(len(domain.owners), 0)

    def test_domain_creation_with_owner(self):
        # You can create a new domain with a single owner.
        domain = self._manager.add('example.org', owners=['anne@example.org'])
        self.assertEqual(len(domain.owners), 1)
        self.assertEqual(domain.owners[0].addresses[0].email,
                         'anne@example.org')

    def test_domain_creation_with_owners(self):
        # You can create a new domain with multiple owners.
        domain = self._manager.add(
            'example.org', owners=['anne@example.org',
                                   'bart@example.net'])
        self.assertEqual(len(domain.owners), 2)
        self.assertEqual(
            sorted(owner.addresses[0].email for owner in domain.owners),
            ['anne@example.org', 'bart@example.net'])

    def test_domain_creation_creates_new_users(self):
        # Domain creation with existing users does not create new users, but
        # any user which doesn't yet exist (and is linked to the given
        # address), gets created.
        user_manager = getUtility(IUserManager)
        user_manager.make_user('anne@example.com')
        user_manager.make_user('bart@example.com')
        domain = self._manager.add(
            'example.org', owners=['anne@example.com',
                                   'bart@example.com',
                                   'cris@example.com'])
        self.assertEqual(len(domain.owners), 3)
        self.assertEqual(
            sorted(owner.addresses[0].email for owner in domain.owners),
            ['anne@example.com', 'bart@example.com', 'cris@example.com'])
        # Now cris exists as a user.
        self.assertIsNotNone(user_manager.get_user('cris@example.com'))

    def test_domain_creation_with_users(self):
        # Domains can be created with IUser objects.
        user_manager = getUtility(IUserManager)
        anne = user_manager.make_user('anne@example.com')
        bart = user_manager.make_user('bart@example.com')
        domain = self._manager.add('example.org', owners=[anne, bart])
        self.assertEqual(len(domain.owners), 2)
        self.assertEqual(
            sorted(owner.addresses[0].email for owner in domain.owners),
            ['anne@example.com', 'bart@example.com'])
        def sort_key(owner):                               # noqa: E306
            return owner.addresses[0].email
        self.assertEqual(sorted(domain.owners, key=sort_key), [anne, bart])

    def test_add_domain_owner(self):
        # Domain owners can be added after the domain is created.
        domain = self._manager.add('example.org')
        self.assertEqual(len(domain.owners), 0)
        domain.add_owner('anne@example.org')
        self.assertEqual(len(domain.owners), 1)
        self.assertEqual(domain.owners[0].addresses[0].email,
                         'anne@example.org')

    def test_add_multiple_domain_owners(self):
        # Multiple domain owners can be added after the domain is created.
        domain = self._manager.add('example.org')
        self.assertEqual(len(domain.owners), 0)
        domain.add_owners(['anne@example.org', 'bart@example.net'])
        self.assertEqual(len(domain.owners), 2)
        self.assertEqual([owner.addresses[0].email for owner in domain.owners],
                         ['anne@example.org', 'bart@example.net'])

    def test_remove_domain_owner(self):
        # Domain onwers can be removed.
        domain = self._manager.add(
            'example.org', owners=['anne@example.org',
                                   'bart@example.net'])
        domain.remove_owner('anne@example.org')
        self.assertEqual(len(domain.owners), 1)
        self.assertEqual([owner.addresses[0].email for owner in domain.owners],
                         ['bart@example.net'])

    def test_remove_missing_owner(self):
        # Users which aren't owners can't be removed.
        domain = self._manager.add(
            'example.org', owners=['anne@example.org',
                                   'bart@example.net'])
        self.assertRaises(ValueError, domain.remove_owner, 'cris@example.org')
        self.assertEqual(len(domain.owners), 2)
        self.assertEqual([owner.addresses[0].email for owner in domain.owners],
                         ['anne@example.org', 'bart@example.net'])


class TestDomainLifecycleEvents(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._domainmanager = getUtility(IDomainManager)
        self._org = self._domainmanager.add('example.net')
        self._net = self._domainmanager.add('example.org')

    def test_lists_are_deleted_when_domain_is_deleted(self):
        # When a domain is deleted, all the mailing lists in that domain are
        # also deleted.
        create_list('ant@example.net')
        create_list('bee@example.net')
        cat = create_list('cat@example.org')
        dog = create_list('dog@example.org')
        ewe = create_list('ewe@example.com')
        fly = create_list('fly@example.com')
        listmanager = getUtility(IListManager)
        self._domainmanager.remove('example.net')
        self.assertEqual(listmanager.get('ant@example.net'), None)
        self.assertEqual(listmanager.get('bee@example.net'), None)
        self.assertEqual(listmanager.get('cat@example.org'), cat)
        self.assertEqual(listmanager.get('dog@example.org'), dog)
        self.assertEqual(listmanager.get('ewe@example.com'), ewe)
        self.assertEqual(listmanager.get('fly@example.com'), fly)
        self._domainmanager.remove('example.org')
        self.assertEqual(listmanager.get('cat@example.org'), None)
        self.assertEqual(listmanager.get('dog@example.org'), None)
        self.assertEqual(listmanager.get('ewe@example.com'), ewe)
        self.assertEqual(listmanager.get('fly@example.com'), fly)
