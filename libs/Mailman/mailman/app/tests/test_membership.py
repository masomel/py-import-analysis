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

"""Tests of application level membership functions."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.app.membership import add_member, delete_member
from mailman.core.constants import system_preferences
from mailman.interfaces.bans import IBanManager
from mailman.interfaces.member import (
    AlreadySubscribedError, DeliveryMode, MemberRole, MembershipIsBannedError,
    NotAMemberError)
from mailman.interfaces.subscriptions import RequestRecord
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import now
from zope.component import getUtility


class TestAddMember(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')

    def test_add_member_new_user(self):
        # Test subscribing a user to a mailing list when the email address has
        # not yet been associated with a user.
        member = add_member(
            self._mlist,
            RequestRecord('aperson@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language))
        self.assertEqual(member.address.email, 'aperson@example.com')
        self.assertEqual(member.list_id, 'test.example.com')
        self.assertEqual(member.role, MemberRole.member)

    def test_add_member_existing_user(self):
        # Test subscribing a user to a mailing list when the email address has
        # already been associated with a user.
        user_manager = getUtility(IUserManager)
        user_manager.create_user('aperson@example.com', 'Anne Person')
        member = add_member(
            self._mlist,
            RequestRecord('aperson@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language))
        self.assertEqual(member.address.email, 'aperson@example.com')
        self.assertEqual(member.list_id, 'test.example.com')

    def test_add_member_banned(self):
        # Test that members who are banned by specific address cannot
        # subscribe to the mailing list.
        IBanManager(self._mlist).ban('anne@example.com')
        with self.assertRaises(MembershipIsBannedError) as cm:
            add_member(
                self._mlist,
                RequestRecord('anne@example.com', 'Anne Person',
                              DeliveryMode.regular,
                              system_preferences.preferred_language))
        self.assertEqual(
            str(cm.exception),
            'anne@example.com is not allowed to subscribe to test@example.com')

    def test_add_member_globally_banned(self):
        # Test that members who are banned by specific address cannot
        # subscribe to the mailing list.
        IBanManager(None).ban('anne@example.com')
        self.assertRaises(
            MembershipIsBannedError,
            add_member, self._mlist,
            RequestRecord('anne@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language))

    def test_add_member_banned_from_different_list(self):
        # Test that members who are banned by on a different list can still be
        # subscribed to other mlists.
        sample_list = create_list('sample@example.com')
        IBanManager(sample_list).ban('anne@example.com')
        member = add_member(
            self._mlist,
            RequestRecord('anne@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language))
        self.assertEqual(member.address.email, 'anne@example.com')

    def test_add_member_banned_by_pattern(self):
        # Addresses matching regexp ban patterns cannot subscribe.
        IBanManager(self._mlist).ban('^.*@example.com')
        self.assertRaises(
            MembershipIsBannedError,
            add_member, self._mlist,
            RequestRecord('anne@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language))

    def test_add_member_globally_banned_by_pattern(self):
        # Addresses matching global regexp ban patterns cannot subscribe.
        IBanManager(None).ban('^.*@example.com')
        self.assertRaises(
            MembershipIsBannedError,
            add_member, self._mlist,
            RequestRecord('anne@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language))

    def test_add_member_banned_from_different_list_by_pattern(self):
        # Addresses matching regexp ban patterns on one list can still
        # subscribe to other mailing lists.
        sample_list = create_list('sample@example.com')
        IBanManager(sample_list).ban('^.*@example.com')
        member = add_member(
            self._mlist,
            RequestRecord('anne@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language))
        self.assertEqual(member.address.email, 'anne@example.com')

    def test_add_member_moderator(self):
        # Test adding a moderator to a mailing list.
        member = add_member(
            self._mlist,
            RequestRecord('aperson@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language),
            MemberRole.moderator)
        self.assertEqual(member.address.email, 'aperson@example.com')
        self.assertEqual(member.list_id, 'test.example.com')
        self.assertEqual(member.role, MemberRole.moderator)

    def test_add_member_twice(self):
        # Adding a member with the same role twice causes an
        # AlreadySubscribedError to be raised.
        add_member(
            self._mlist,
            RequestRecord('aperson@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language),
            MemberRole.member)
        with self.assertRaises(AlreadySubscribedError) as cm:
            add_member(
                self._mlist,
                RequestRecord('aperson@example.com', 'Anne Person',
                              DeliveryMode.regular,
                              system_preferences.preferred_language),
                MemberRole.member)
        self.assertEqual(cm.exception.fqdn_listname, 'test@example.com')
        self.assertEqual(cm.exception.email, 'aperson@example.com')
        self.assertEqual(cm.exception.role, MemberRole.member)

    def test_add_member_with_different_roles(self):
        # Adding a member twice with different roles is okay.
        member_1 = add_member(
            self._mlist,
            RequestRecord('aperson@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language),
            MemberRole.member)
        member_2 = add_member(
            self._mlist,
            RequestRecord('aperson@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language),
            MemberRole.owner)
        self.assertEqual(member_1.list_id, member_2.list_id)
        self.assertEqual(member_1.address, member_2.address)
        self.assertEqual(member_1.user, member_2.user)
        self.assertNotEqual(member_1.member_id, member_2.member_id)
        self.assertEqual(member_1.role, MemberRole.member)
        self.assertEqual(member_2.role, MemberRole.owner)

    def test_add_member_with_mixed_case_email(self):
        # LP: #1425359 - Mailman is case-perserving, case-insensitive.  This
        # test subscribes the lower case address and ensures the original
        # mixed case address can't be subscribed.
        email = 'APerson@example.com'
        add_member(
            self._mlist,
            RequestRecord(email.lower(), 'Ann Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language))
        with self.assertRaises(AlreadySubscribedError) as cm:
            add_member(
                self._mlist,
                RequestRecord(email, 'Ann Person',
                              DeliveryMode.regular,
                              system_preferences.preferred_language))
        self.assertEqual(cm.exception.email, email)

    def test_add_member_with_lower_case_email(self):
        # LP: #1425359 - Mailman is case-perserving, case-insensitive.  This
        # test subscribes the mixed case address and ensures the lower cased
        # address can't be added.
        email = 'APerson@example.com'
        add_member(
            self._mlist,
            RequestRecord(email, 'Ann Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language))
        with self.assertRaises(AlreadySubscribedError) as cm:
            add_member(
                self._mlist,
                RequestRecord(email.lower(), 'Ann Person',
                              DeliveryMode.regular,
                              system_preferences.preferred_language))
        self.assertEqual(cm.exception.email, email.lower())

    def test_delete_nonmembers_on_adding_member(self):
        # GL: #237 - When a new address is subscribed, any existing nonmember
        # subscriptions for this address; or any addresses also controlled by
        # this user, are deleted.
        anne_nonmember = add_member(
            self._mlist,
            RequestRecord('aperson@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language),
            MemberRole.nonmember)
        # Add a few other validated addresses to this user, and subscribe them
        # as nonmembers.
        for email in ('anne.person@example.com', 'a.person@example.com'):
            address = anne_nonmember.user.register(email)
            address.verified_on = now()
            self._mlist.subscribe(address, MemberRole.nonmember)
        # There are now three nonmembers.
        self.assertEqual(
            {address.email for address in self._mlist.nonmembers.addresses},
            {'aperson@example.com',
             'anne.person@example.com',
             'a.person@example.com',
             })
        # Let's now add one of Anne's addresses as a member.  This deletes all
        # of Anne's nonmember memberships.
        anne_member = add_member(
            self._mlist,
            RequestRecord('a.person@example.com', 'Anne Person',
                          DeliveryMode.regular,
                          system_preferences.preferred_language),
            MemberRole.member)
        self.assertEqual(self._mlist.nonmembers.member_count, 0)
        members = list(self._mlist.members.members)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0], anne_member)


class TestDeleteMember(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')

    def test_delete_member_not_a_member(self):
        # Try to delete an address which is not a member of the mailing list.
        with self.assertRaises(NotAMemberError) as cm:
            delete_member(self._mlist, 'noperson@example.com')
        self.assertEqual(
            str(cm.exception),
            'noperson@example.com is not a member of test@example.com')
