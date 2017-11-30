# Copyright (C) 2012-2017 by the Free Software Foundation, Inc.
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

"""Test rosters."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.interfaces.address import IAddress
from mailman.interfaces.member import DeliveryMode, MemberRole
from mailman.interfaces.user import IUser
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import set_preferred
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestMailingListRoster(unittest.TestCase):
    """Test various aspects of a mailing list's roster."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        user_manager = getUtility(IUserManager)
        self._anne = user_manager.create_address('anne@example.com')
        self._bart = user_manager.create_address('bart@example.com')
        self._cris = user_manager.create_address('cris@example.com')

    def test_no_members(self):
        # Nobody with any role is subscribed to the mailing list.
        self.assertEqual(self._mlist.owners.member_count, 0)
        self.assertEqual(self._mlist.moderators.member_count, 0)
        self.assertEqual(self._mlist.administrators.member_count, 0)
        self.assertEqual(self._mlist.members.member_count, 0)
        self.assertEqual(self._mlist.regular_members.member_count, 0)
        self.assertEqual(self._mlist.digest_members.member_count, 0)
        self.assertEqual(self._mlist.subscribers.member_count, 0)

    def test_one_regular_member(self):
        # One person getting regular delivery is subscribed to the mailing
        # list as a member.
        self._mlist.subscribe(self._anne, role=MemberRole.member)
        self.assertEqual(self._mlist.owners.member_count, 0)
        self.assertEqual(self._mlist.moderators.member_count, 0)
        self.assertEqual(self._mlist.administrators.member_count, 0)
        self.assertEqual(self._mlist.members.member_count, 1)
        self.assertEqual(self._mlist.regular_members.member_count, 1)
        self.assertEqual(self._mlist.digest_members.member_count, 0)
        self.assertEqual(self._mlist.subscribers.member_count, 1)

    def test_two_regular_members(self):
        # Two people getting regular delivery are subscribed to the mailing
        # list as members.
        self._mlist.subscribe(self._anne, role=MemberRole.member)
        self._mlist.subscribe(self._bart, role=MemberRole.member)
        self.assertEqual(self._mlist.owners.member_count, 0)
        self.assertEqual(self._mlist.moderators.member_count, 0)
        self.assertEqual(self._mlist.administrators.member_count, 0)
        self.assertEqual(self._mlist.members.member_count, 2)
        self.assertEqual(self._mlist.regular_members.member_count, 2)
        self.assertEqual(self._mlist.digest_members.member_count, 0)
        self.assertEqual(self._mlist.subscribers.member_count, 2)

    def test_one_regular_members_one_digest_member(self):
        # Two people are subscribed to the mailing list as members.  One gets
        # regular delivery and one gets digest delivery.
        self._mlist.subscribe(self._anne, role=MemberRole.member)
        member = self._mlist.subscribe(self._bart, role=MemberRole.member)
        member.preferences.delivery_mode = DeliveryMode.mime_digests
        self.assertEqual(self._mlist.owners.member_count, 0)
        self.assertEqual(self._mlist.moderators.member_count, 0)
        self.assertEqual(self._mlist.administrators.member_count, 0)
        self.assertEqual(self._mlist.members.member_count, 2)
        self.assertEqual(self._mlist.regular_members.member_count, 1)
        self.assertEqual(self._mlist.digest_members.member_count, 1)
        self.assertEqual(self._mlist.subscribers.member_count, 2)

    def test_a_person_is_both_a_member_and_an_owner(self):
        # Anne is the owner of a mailing list and she gets subscribed as a
        # member of the mailing list, receiving regular deliveries.
        self._mlist.subscribe(self._anne, role=MemberRole.member)
        self._mlist.subscribe(self._anne, role=MemberRole.owner)
        self.assertEqual(self._mlist.owners.member_count, 1)
        self.assertEqual(self._mlist.moderators.member_count, 0)
        self.assertEqual(self._mlist.administrators.member_count, 1)
        self.assertEqual(self._mlist.members.member_count, 1)
        self.assertEqual(self._mlist.regular_members.member_count, 1)
        self.assertEqual(self._mlist.digest_members.member_count, 0)
        self.assertEqual(self._mlist.subscribers.member_count, 2)

    def test_a_bunch_of_members_and_administrators(self):
        # Anne is the owner of a mailing list, and Bart is a moderator.  Anne
        # gets subscribed as a member of the mailing list, receiving regular
        # deliveries.  Cris subscribes to the mailing list as a digest member.
        self._mlist.subscribe(self._anne, role=MemberRole.owner)
        self._mlist.subscribe(self._bart, role=MemberRole.moderator)
        self._mlist.subscribe(self._anne, role=MemberRole.member)
        member = self._mlist.subscribe(self._cris, role=MemberRole.member)
        member.preferences.delivery_mode = DeliveryMode.mime_digests
        self.assertEqual(self._mlist.owners.member_count, 1)
        self.assertEqual(self._mlist.moderators.member_count, 1)
        self.assertEqual(self._mlist.administrators.member_count, 2)
        self.assertEqual(self._mlist.members.member_count, 2)
        self.assertEqual(self._mlist.regular_members.member_count, 1)
        self.assertEqual(self._mlist.digest_members.member_count, 1)
        self.assertEqual(self._mlist.subscribers.member_count, 4)


class TestMembershipsRoster(unittest.TestCase):
    """Test the memberships roster."""

    layer = ConfigLayer

    def setUp(self):
        self._ant = create_list('ant@example.com')
        self._bee = create_list('bee@example.com')
        user_manager = getUtility(IUserManager)
        self._anne = user_manager.make_user(
            'anne@example.com', 'Anne Person')
        set_preferred(self._anne)

    def test_no_memberships(self):
        # An unsubscribed user has no memberships.
        self.assertEqual(self._anne.memberships.member_count, 0)
        self.assertIsNone(self._ant.members.get_member('anne@example.com'))
        self.assertEqual(
            self._ant.members.get_memberships('anne@example.com'),
            [])

    def test_subscriptions(self):
        # Anne subscribes to a couple of mailing lists.
        self._ant.subscribe(self._anne)
        self._bee.subscribe(self._anne)
        self.assertEqual(self._anne.memberships.member_count, 2)

    def test_subscribed_as_user(self):
        # Anne subscribes to a mailing list as a user and the member roster
        # contains her membership.
        self._ant.subscribe(self._anne)
        self.assertEqual(
            self._ant.members.get_member('anne@example.com').user,
            self._anne)
        memberships = self._ant.members.get_memberships('anne@example.com')
        self.assertEqual(
            [member.address.email for member in memberships],
            ['anne@example.com'])

    def test_subscribed_as_user_and_address(self):
        # Anne subscribes to a mailing list twice, once as a user and once
        # with an explicit address.  She has two memberships.
        self._ant.subscribe(self._anne)
        self._ant.subscribe(self._anne.preferred_address)
        self.assertEqual(self._anne.memberships.member_count, 2)
        self.assertEqual(self._ant.members.member_count, 2)
        self.assertEqual(
            [member.address.email for member in self._ant.members.members],
            ['anne@example.com', 'anne@example.com'])
        # get_member() is defined to return the explicit address.
        member = self._ant.members.get_member('anne@example.com')
        subscriber = member.subscriber
        self.assertTrue(IAddress.providedBy(subscriber))
        self.assertFalse(IUser.providedBy(subscriber))
        # get_memberships() returns them all.
        memberships = self._ant.members.get_memberships('anne@example.com')
        self.assertEqual(len(memberships), 2)
        as_address = (memberships[0]
                      if IAddress.providedBy(memberships[0].subscriber)
                      else memberships[1])
        as_user = (memberships[1]
                   if IUser.providedBy(memberships[1].subscriber)
                   else memberships[0])
        self.assertEqual(as_address.subscriber, self._anne.preferred_address)
        self.assertEqual(as_user.subscriber, self._anne)
        # All the email addresses match.
        self.assertEqual(
            [record.address.email for record in memberships],
            ['anne@example.com', 'anne@example.com'])

    def test_memberships_users(self):
        self._ant.subscribe(self._anne)
        users = list(self._anne.memberships.users)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0], self._anne)


class TestUserRoster(unittest.TestCase):
    """Test aspects of rosters when users are subscribed."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        user_manager = getUtility(IUserManager)
        self._anne = user_manager.create_user('anne@example.com')
        self._bart = user_manager.create_user('bart@example.com')
        self._cris = user_manager.create_user('cris@example.com')
        self._dave = user_manager.create_user('dave@example.com')
        set_preferred(self._anne)
        set_preferred(self._bart)
        set_preferred(self._cris)
        set_preferred(self._dave)

    def test_narrow_get_member(self):
        # Ensure that when multiple users are subscribed to the same mailing
        # list via their preferred address, only the member in question is
        # returned from .get_member().
        self._mlist.subscribe(self._anne)
        self._mlist.subscribe(self._bart)
        self._mlist.subscribe(self._cris)
        self._mlist.subscribe(self._dave)
        member = self._mlist.members.get_member('bart@example.com')
        self.assertEqual(member.user, self._bart)
