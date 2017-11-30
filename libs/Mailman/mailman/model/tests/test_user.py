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

"""Test users."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.database.transaction import transaction
from mailman.interfaces.address import (
    AddressAlreadyLinkedError, AddressNotLinkedError)
from mailman.interfaces.member import MemberRole
from mailman.interfaces.user import UnverifiedAddressError
from mailman.interfaces.usermanager import IUserManager
from mailman.model.preferences import Preferences
from mailman.testing.helpers import set_preferred
from mailman.testing.layers import ConfigLayer
from sqlalchemy import inspect
from zope.component import getUtility


class TestUser(unittest.TestCase):
    """Test users."""

    layer = ConfigLayer

    def setUp(self):
        self._manager = getUtility(IUserManager)
        self._mlist = create_list('test@example.com')
        self._anne = self._manager.create_user(
            'anne@example.com', 'Anne Person')
        set_preferred(self._anne)

    def test_preferred_address_memberships(self):
        self._mlist.subscribe(self._anne)
        memberships = list(self._anne.memberships.members)
        self.assertEqual(len(memberships), 1)
        self.assertEqual(memberships[0].address.email, 'anne@example.com')
        self.assertEqual(memberships[0].user, self._anne)
        addresses = list(self._anne.memberships.addresses)
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0].email, 'anne@example.com')

    def test_preferred_and_address_memberships(self):
        self._mlist.subscribe(self._anne)
        aperson = self._anne.register('aperson@example.com')
        self._mlist.subscribe(aperson)
        memberships = list(self._anne.memberships.members)
        self.assertEqual(len(memberships), 2)
        self.assertEqual(set(member.address.email for member in memberships),
                         set(['anne@example.com', 'aperson@example.com']))
        self.assertEqual(memberships[0].user, memberships[1].user)
        self.assertEqual(memberships[0].user, self._anne)
        emails = set(address.email
                     for address in self._anne.memberships.addresses)
        self.assertEqual(len(emails), 2)
        self.assertEqual(emails,
                         set(['anne@example.com', 'aperson@example.com']))

    def test_uid_is_immutable(self):
        with self.assertRaises(AttributeError):
            self._anne.user_id = 'foo'

    def test_addresses_may_only_be_linked_to_one_user(self):
        user = self._manager.create_user()
        # Anne's preferred address is already linked to her.
        with self.assertRaises(AddressAlreadyLinkedError) as cm:
            user.link(self._anne.preferred_address)
        self.assertEqual(cm.exception.address, self._anne.preferred_address)

    def test_unlink_from_address_not_linked_to(self):
        # You cannot unlink an address from a user if that address is not
        # already linked to the user.
        user = self._manager.create_user()
        with self.assertRaises(AddressNotLinkedError) as cm:
            user.unlink(self._anne.preferred_address)
        self.assertEqual(cm.exception.address, self._anne.preferred_address)

    def test_unlink_address_which_is_not_linked(self):
        # You cannot unlink an address which is not linked to any user.
        address = self._manager.create_address('bart@example.com')
        user = self._manager.create_user()
        with self.assertRaises(AddressNotLinkedError) as cm:
            user.unlink(address)
        self.assertEqual(cm.exception.address, address)

    def test_set_unverified_preferred_address(self):
        # A user's preferred address cannot be set to an unverified address.
        new_preferred = self._manager.create_address(
            'anne.person@example.com')
        with self.assertRaises(UnverifiedAddressError) as cm:
            self._anne.preferred_address = new_preferred
        self.assertEqual(cm.exception.address, new_preferred)

    def test_preferences_deletion_on_user_deletion(self):
        # LP: #1418276 - deleting a user did not delete their preferences.
        with transaction():
            # This has to happen in a transaction so that both the user and
            # the preferences objects get valid ids.
            user = self._manager.create_user()
        # The user's preference is in the database.
        preferences = config.db.store.query(Preferences).filter_by(
            id=user.preferences.id)
        self.assertEqual(preferences.count(), 1)
        self._manager.delete_user(user)
        # The user's preference has been deleted.
        preferences = config.db.store.query(Preferences).filter_by(
            id=user.preferences.id)
        self.assertEqual(preferences.count(), 0)

    def test_absorb_not_a_user(self):
        bart = self._manager.create_address('bart@example.com')
        self.assertRaises(TypeError, self._anne.absorb, bart)

    def test_absorb_addresses(self):
        # Absorbing the user absorbs all of the users addresses.  I.e. they
        # are relinked to the absorbing user.
        anne_preferred = self._anne.preferred_address
        with transaction():
            # This has to happen in a transaction so that both the user and
            # the preferences objects get valid ids.
            bart = self._manager.create_user('bart@example.com', 'Bart Person')
            bart_secondary = self._manager.create_address(
                'bart.person@example.com')
            bart.link(bart_secondary)
        # Absorb the Bart user into Anne.
        self._anne.absorb(bart)
        # Bart's primary and secondary addresses are now linked to Anne.
        anne_addresses = list(
            address.email for address in self._anne.addresses)
        self.assertIn('bart@example.com', anne_addresses)
        self.assertIn('bart.person@example.com', anne_addresses)
        # Anne's preferred address shouldn't change.
        self.assertEqual(self._anne.preferred_address, anne_preferred)
        # Check the reverse linkages by getting Bart's addresses from the user
        # manager.  They should both point back to the Anne user.
        self.assertEqual(
            self._manager.get_user('bart@example.com'), self._anne)
        self.assertEqual(
            self._manager.get_user('bart.person@example.com'), self._anne)
        # The Bart user has been deleted.
        self.assertIsNone(self._manager.get_user_by_id(bart.user_id))

    def test_absorb_memberships(self):
        # When a user is absorbed, all of their user-subscribed memberships
        # are relinked to the absorbing user.
        mlist2 = create_list('test2@example.com')
        mlist3 = create_list('test3@example.com')
        with transaction():
            # This has to happen in a transaction so that both the user and
            # the preferences objects get valid ids.
            bart = self._manager.create_user('bart@example.com', 'Bart Person')
            set_preferred(bart)
        # Subscribe both users to self._mlist.
        self._mlist.subscribe(self._anne, MemberRole.member)
        self._mlist.subscribe(bart, MemberRole.moderator)
        # Subscribe only Bart to mlist2.
        mlist2.subscribe(bart, MemberRole.owner)
        # Subscribe only Bart's address to mlist3.
        mlist3.subscribe(bart.preferred_address, MemberRole.moderator)
        # There are now 4 memberships, one with Anne two with Bart's user and
        # one with Bart's address.
        all_members = list(self._manager.members)
        self.assertEqual(len(all_members), 4, all_members)
        # Do the absorption.
        self._anne.absorb(bart)
        # The Bart user has been deleted, leaving only the Anne user in the
        # user manager.
        all_users = list(self._manager.users)
        self.assertEqual(len(all_users), 1)
        self.assertEqual(all_users[0], self._anne)
        # There are no leftover memberships for user Bart.  Anne owns all the
        # memberships.
        all_members = list(self._manager.members)
        self.assertEqual(len(all_members), 4, all_members)
        self.assertEqual(self._anne.memberships.member_count, 4)
        memberships = {(member.list_id, member.role): member
                       for member in self._anne.memberships.members}
        # Note that Anne is now both a member and moderator of the test list.
        self.assertEqual(set(memberships), set([
            ('test.example.com', MemberRole.member),
            ('test.example.com', MemberRole.moderator),
            ('test2.example.com', MemberRole.owner),
            ('test3.example.com', MemberRole.moderator),
            ]))
        # Both of Bart's previous user subscriptions are now transferred to
        # the Anne user.
        self.assertEqual(
            memberships[('test.example.com', MemberRole.moderator)].address,
            self._anne.preferred_address)
        self.assertEqual(
            memberships[('test2.example.com', MemberRole.owner)].address,
            self._anne.preferred_address)
        # Bart's address was subscribed; it must not have been changed.  Of
        # course, Anne now controls bart@example.com.
        key = ('test3.example.com', MemberRole.moderator)
        self.assertEqual(memberships[key].address.email, 'bart@example.com')
        self.assertEqual(self._manager.get_user('bart@example.com'),
                         self._anne)

    def test_absorb_duplicates(self):
        # Duplicate memberships, where the list-id and role match, are
        # ignored.  Here we subscribe Anne to the test list as a member, and
        # Bart as both a member and an owner.  Anne's member membership
        # remains unchanged, but she gains an owner membership.
        with transaction():
            bart = self._manager.create_user('bart@example.com')
            set_preferred(bart)
        self._mlist.subscribe(self._anne, MemberRole.member)
        self._mlist.subscribe(bart, MemberRole.member)
        self._mlist.subscribe(bart, MemberRole.owner)
        # There are now three memberships.
        all_members = list(self._manager.members)
        self.assertEqual(len(all_members), 3, all_members)
        # Do the absorption.
        self._anne.absorb(bart)
        # There are now only 2 memberships, both owned by Anne.
        all_members = list(self._manager.members)
        self.assertEqual(len(all_members), 2, all_members)
        memberships = set([
            (member.list_id, member.role, member.address.email)
            for member in all_members
            ])
        self.assertEqual(memberships, set([
            ('test.example.com', MemberRole.member, 'anne@example.com'),
            ('test.example.com', MemberRole.owner, 'anne@example.com'),
            ]))

    def test_absorb_preferences(self):
        with transaction():
            # This has to happen in a transaction so that both the user and
            # the preferences objects get valid ids.
            bart = self._manager.create_user('bart@example.com', 'Bart Person')
        bart.preferences.acknowledge_posts = True
        self.assertIsNone(self._anne.preferences.acknowledge_posts)
        self._anne.absorb(bart)
        self.assertEqual(self._anne.preferences.acknowledge_posts, True)
        # Check that Bart's preferences were deleted (requires a DB flush).
        config.db.store.flush()
        self.assertTrue(inspect(bart.preferences).deleted)

    def test_absorb_properties(self):
        properties = {
            'password': 'dummy',
            'is_server_owner': True
            }
        with transaction():
            # This has to happen in a transaction so that both the user and
            # the preferences objects get valid ids.
            bart = self._manager.create_user('bart@example.com', 'Bart Person')
        for name, value in properties.items():
            setattr(bart, name, value)
        self._anne.absorb(bart)
        for name, value in properties.items():
            self.assertEqual(getattr(self._anne, name), value)
        # This was not empty so it must not have been overwritten.
        self.assertEqual(self._anne.display_name, 'Anne Person')

    def test_absorb_display_name(self):
        # Bart has no display name, but once he absorbs Cate, he gains her
        # display_name.
        with transaction():
            bart = self._manager.create_user('bart@example.com')
            cate = self._manager.create_user('cate@example.com', 'Cate Person')
        self.assertEqual(bart.display_name, '')
        bart.absorb(cate)
        self.assertEqual(bart.display_name, 'Cate Person')

    def test_absorb_delete_user(self):
        # Make sure the user was deleted after being absorbed.
        with transaction():
            # This has to happen in a transaction so that both the user and
            # the preferences objects get valid ids.
            bart = self._manager.create_user('bart@example.com', 'Bart Person')
        bart_user_id = bart.user_id
        self._anne.absorb(bart)
        self.assertIsNone(self._manager.get_user_by_id(bart_user_id))

    def test_absorb_self(self):
        # Absorbing oneself should be a no-op (it must not delete the user).
        self._mlist.subscribe(self._anne)
        self._anne.absorb(self._anne)
        new_anne = self._manager.get_user_by_id(self._anne.user_id)
        self.assertIsNotNone(new_anne)
        self.assertEqual(
            [address.email for address in new_anne.addresses],
            ['anne@example.com'])
        self.assertEqual(new_anne.memberships.member_count, 1)
