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

"""Test the subscription service."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.interfaces.listmanager import NoSuchListError
from mailman.interfaces.member import MemberRole
from mailman.interfaces.subscriptions import (
    ISubscriptionService, TooManyMembersError)
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import set_preferred, subscribe
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import now
from zope.component import getUtility


class TestSubscriptionService(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._mlist.admin_immed_notify = False
        self._user_manager = getUtility(IUserManager)
        self._service = getUtility(ISubscriptionService)

    def test_find_member_address_no_user(self):
        # Find address-based memberships when no user is linked to the address.
        address = self._user_manager.create_address(
            'anne@example.com', 'Anne Address')
        self._mlist.subscribe(address)
        members = self._service.find_members('anne@example.com')
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].address, address)

    def test_find_member_address_with_user(self):
        # Find address-based memberships when a user is linked to the address.
        user = self._user_manager.create_user(
            'anne@example.com', 'Anne User')
        address = set_preferred(user)
        # Subscribe the address.
        self._mlist.subscribe(address)
        members = self._service.find_members('anne@example.com')
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].user, user)

    def test_find_member_user(self):
        # Find user-based memberships by address.
        user = self._user_manager.create_user(
            'anne@example.com', 'Anne User')
        set_preferred(user)
        # Subscribe the user.
        self._mlist.subscribe(user)
        members = self._service.find_members('anne@example.com')
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].user, user)

    def test_wont_find_member_user_secondary_address(self):
        # Finding user-based memberships using a secondary address is not
        # supported; the subscription is not returned.
        user = self._user_manager.create_user(
            'anne@example.com', 'Anne User')
        set_preferred(user)
        # Create a secondary address.
        address_2 = self._user_manager.create_address(
            'anne2@example.com', 'Anne User 2')
        address_2.user = user
        # Subscribe the user.
        self._mlist.subscribe(user)
        # Search for the secondary address.
        members = self._service.find_members('anne2@example.com')
        self.assertEqual(len(members), 0)

    def test_wont_find_member_secondary_address(self):
        # A user is subscribed with one of their address, and a search is
        # performed on another of their addresses.  This is not supported; the
        # subscription is not returned.
        user = self._user_manager.create_user(
            'anne@example.com', 'Anne User')
        set_preferred(user)
        # Create a secondary address.
        address_2 = self._user_manager.create_address(
            'anne2@example.com', 'Anne User 2')
        address_2.verified_on = now()
        address_2.user = user
        # Subscribe the secondary address.
        self._mlist.subscribe(address_2)
        # Search for the primary address.
        members = self._service.find_members('anne@example.com')
        self.assertEqual(len(members), 0)

    def test_find_member_user_id(self):
        # Find user-based memberships by user_id.
        user = self._user_manager.create_user(
            'anne@example.com', 'Anne User')
        set_preferred(user)
        # Subscribe the user.
        self._mlist.subscribe(user)
        members = self._service.find_members(user.user_id)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].user, user)

    def test_find_member_user_id_controlled_addresses(self):
        # Find address-based memberships by user_id when a secondary address is
        # subscribed.
        user = self._user_manager.create_user(
            'anne@example.com', 'Anne User')
        set_preferred(user)
        # Create a secondary address.
        address_2 = self._user_manager.create_address(
            'anne2@example.com', 'Anne User 2')
        address_2.verified_on = now()
        address_2.user = user
        # Create a third address.
        address_3 = self._user_manager.create_address(
            'anne3@example.com', 'Anne User 3')
        address_3.verified_on = now()
        address_3.user = user
        # Subscribe the secondary address only.
        self._mlist.subscribe(address_2)
        members = self._service.find_members(user.user_id)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].address, address_2)

    def test_find_member_sorting(self):
        # Check that the memberships are properly sorted.
        user = self._user_manager.create_user(
            'anne1@example.com', 'Anne User')
        address = set_preferred(user)
        # Create a secondary address.
        address_2 = self._user_manager.create_address(
            'anne2@example.com', 'Anne User 2')
        address_2.verified_on = now()
        address_2.user = user
        # Create a third address.
        address_3 = self._user_manager.create_address(
            'anne3@example.com', 'Anne User 3')
        address_3.verified_on = now()
        address_3.user = user
        # Create three lists.
        mlist1 = create_list('test1@example.com')
        mlist1.admin_immed_notify = False
        mlist2 = create_list('test2@example.com')
        mlist2.admin_immed_notify = False
        mlist3 = create_list('test3@example.com')
        mlist3.admin_immed_notify = False
        # Subscribe the addresses in random order
        # https://www.xkcd.com/221/
        mlist3.subscribe(address_3, MemberRole.moderator)
        mlist3.subscribe(address_3, MemberRole.owner)
        mlist3.subscribe(address_3, MemberRole.member)
        mlist3.subscribe(address_2, MemberRole.member)
        mlist3.subscribe(address_2, MemberRole.owner)
        mlist3.subscribe(address_2, MemberRole.moderator)
        mlist3.subscribe(address, MemberRole.owner)
        mlist3.subscribe(address, MemberRole.member)
        mlist3.subscribe(address, MemberRole.moderator)
        mlist2.subscribe(address_2, MemberRole.moderator)
        mlist2.subscribe(address_2, MemberRole.member)
        mlist2.subscribe(address_2, MemberRole.owner)
        mlist2.subscribe(address_3, MemberRole.moderator)
        mlist2.subscribe(address_3, MemberRole.member)
        mlist2.subscribe(address_3, MemberRole.owner)
        mlist2.subscribe(address, MemberRole.owner)
        mlist2.subscribe(address, MemberRole.moderator)
        mlist2.subscribe(address, MemberRole.member)
        mlist1.subscribe(address_2, MemberRole.moderator)
        mlist1.subscribe(address, MemberRole.member)
        mlist1.subscribe(address_3, MemberRole.owner)
        # The results should be sorted first by list id, then by address, then
        # by member role.
        members = self._service.find_members(user.user_id)
        self.assertEqual(len(members), 21)
        self.assertListEqual(
            [(m.list_id.partition('.')[0],
              m.address.email.partition('@')[0],
              m.role)
             for m in members],
            [('test1', 'anne1', MemberRole.member),
             ('test1', 'anne2', MemberRole.moderator),
             ('test1', 'anne3', MemberRole.owner),
             ('test2', 'anne1', MemberRole.member),
             ('test2', 'anne1', MemberRole.owner),
             ('test2', 'anne1', MemberRole.moderator),
             ('test2', 'anne2', MemberRole.member),
             ('test2', 'anne2', MemberRole.owner),
             ('test2', 'anne2', MemberRole.moderator),
             ('test2', 'anne3', MemberRole.member),
             ('test2', 'anne3', MemberRole.owner),
             ('test2', 'anne3', MemberRole.moderator),
             ('test3', 'anne1', MemberRole.member),
             ('test3', 'anne1', MemberRole.owner),
             ('test3', 'anne1', MemberRole.moderator),
             ('test3', 'anne2', MemberRole.member),
             ('test3', 'anne2', MemberRole.owner),
             ('test3', 'anne2', MemberRole.moderator),
             ('test3', 'anne3', MemberRole.member),
             ('test3', 'anne3', MemberRole.owner),
             ('test3', 'anne3', MemberRole.moderator),
             ])

    def test_find_no_members(self):
        members = self._service.find_members()
        self.assertEqual(len(members), 0)

    def test_find_members_no_results(self):
        members = self._service.find_members('zack@example.com')
        self.assertEqual(len(members), 0)
        self.assertEqual(list(members), [])

    def test_find_member_error(self):
        # .find_member() can only return zero or one memberships.  Anything
        # else is an error.
        subscribe(self._mlist, 'Anne')
        subscribe(self._mlist, 'Anne', MemberRole.owner)
        with self.assertRaises(TooManyMembersError) as cm:
            self._service.find_member('aperson@example.com')
        self.assertEqual(cm.exception.subscriber, 'aperson@example.com')
        self.assertEqual(cm.exception.list_id, None)
        self.assertEqual(cm.exception.role, None)

    def test_leave_no_such_list(self):
        # Trying to leave a nonexistent list raises an exception.
        self.assertRaises(NoSuchListError, self._service.leave,
                          'bogus.example.com', 'anne@example.com')

    def test_unsubscribe_members_no_such_list(self):
        # Raises an exception if an invalid list_id is passed
        self.assertRaises(NoSuchListError, self._service.unsubscribe_members,
                          'bogus.example.com', ['anne@example.com'])

    def test_unsubscribe_members(self):
        # Check that memberships are properly unsubscribed.
        #
        # Start by creating the mailing lists we'll use.  Make sure that
        # subscriptions don't send any notifications.
        ant = create_list('ant@example.com')
        ant.admin_immed_notify = False
        bee = create_list('bee@example.com')
        bee.admin_immed_notify = False
        # Anne is a user with a preferred address and several linked
        # secondary addresses.
        anne = self._user_manager.create_user('anne_0@example.com')
        anne_0 = set_preferred(anne)
        anne_1 = self._user_manager.create_address('anne_1@example.com')
        anne_1.verified_on = now()
        anne_1.user = anne
        anne_2 = self._user_manager.create_address('anne_2@example.com')
        anne_2.verified_on = now()
        anne_2.user = anne
        # These folks will subscribe with addresses only.
        bart = self._user_manager.create_address('bart@example.com')
        bart.verified_on = now()
        cris = self._user_manager.create_address('cris@example.com')
        cris.verified_on = now()
        dave = self._user_manager.create_address('dave@example.com')
        dave.verified_on = now()
        # Elle is another user with a preferred address and a linked
        # secondary address.
        elle = self._user_manager.create_user('elle_0@example.com')
        elle_0 = set_preferred(elle)
        elle_1 = self._user_manager.create_address('elle_1@example.com')
        elle_1.verified_on = now()
        # Fred will also subscribe with just his address.
        fred = self._user_manager.create_address('fred@example.com')
        # Gwen will only be subscribed to the second mailing list.
        gwen = self._user_manager.create_address('gwen@example.com')
        # Now we're going to create some subscriptions, with various
        # combinations of user or address subscribers, and various
        # roles.
        ant.subscribe(anne, MemberRole.member)
        ant.subscribe(anne, MemberRole.moderator)
        ant.subscribe(anne, MemberRole.owner)
        bee.subscribe(anne, MemberRole.member)
        bee.subscribe(anne, MemberRole.moderator)
        ant.subscribe(anne_0, MemberRole.member)
        bee.subscribe(anne_0, MemberRole.member)
        bee.subscribe(anne_0, MemberRole.moderator)
        ant.subscribe(anne_1, MemberRole.member)
        ant.subscribe(anne_1, MemberRole.moderator)
        bee.subscribe(anne_1, MemberRole.member)
        bee.subscribe(anne_1, MemberRole.owner)
        ant.subscribe(anne_2, MemberRole.member)
        # Now for Bart.
        ant.subscribe(bart, MemberRole.member)
        bee.subscribe(bart, MemberRole.member)
        # And Cris.
        ant.subscribe(cris, MemberRole.member)
        ant.subscribe(cris, MemberRole.moderator)
        bee.subscribe(cris, MemberRole.member)
        # Now Dave.
        ant.subscribe(dave, MemberRole.member)
        bee.subscribe(dave, MemberRole.member)
        bee.subscribe(dave, MemberRole.moderator)
        # Elle-the-user.
        ant.subscribe(elle, MemberRole.member)
        # Elle-the-address.
        bee.subscribe(elle_0, MemberRole.member)
        # Fred and Gwen.
        ant.subscribe(fred, MemberRole.member)
        bee.subscribe(gwen, MemberRole.member)
        # Now it's time to do the mass unsubscribe from the ant mailing
        # list.  We choose a set of addresses that have multiple
        # memberships across both lists, with various roles.  We're only
        # going to unsubscribe those addresses which are subscribed to
        # the ant mailing list with the role of member.  Throw in a few
        # bogus or not-subscribed addresses.
        success, fail = self._service.unsubscribe_members(
            ant.list_id, set([
                'anne_0@example.com',
                'anne_1@example.com',
                'bart@example.com',
                'cris@example.com',
                'fred@example.com',
                'elle_0@example.com',
                'gwen@example.com',
                'bogus@example.com',
                ]))
        # We should have successfully unsubscribed these addresses,
        # which were subscribed in various ways to the ant mailing list
        # as members.
        self.assertEqual(success, set([
            'anne_0@example.com',
            'anne_1@example.com',
            'bart@example.com',
            'cris@example.com',
            'elle_0@example.com',
            'fred@example.com',
            ]))
        # These two addresses were failed, in one case because it's not
        # a valid email address, and in the other because it's not
        # subscribed to the mailing list.
        self.assertEqual(fail, set([
            'bogus@example.com',
            'gwen@example.com',
            ]))
        # Now obtain various rosters and ensure that they have the
        # memberships we expect, after the mass unsubscribe.
        ant_members = ant.get_roster(MemberRole.member)
        self.assertEqual(
            [address.email for address in ant_members.addresses],
            ['anne_2@example.com',
             'dave@example.com',
             ])
        bee_members = bee.get_roster(MemberRole.member)
        # anne_0 is in the list twice, once because she's subscribed
        # with her preferred address, and again because she's subscribed
        # with her explicit address.
        self.assertEqual(
            [address.email for address in bee_members.addresses],
            ['anne_0@example.com',
             'anne_0@example.com',
             'anne_1@example.com',
             'bart@example.com',
             'cris@example.com',
             'dave@example.com',
             'elle_0@example.com',
             'gwen@example.com',
             ])
        ant_moderators = ant.get_roster(MemberRole.moderator)
        self.assertEqual(
            [address.email for address in ant_moderators.addresses],
            ['anne_0@example.com',
             'anne_1@example.com',
             'cris@example.com',
             ])
        bee_moderators = bee.get_roster(MemberRole.moderator)
        # As above, anne_0 shows up the moderators twice.
        self.assertEqual(
            [address.email for address in bee_moderators.addresses],
            ['anne_0@example.com',
             'anne_0@example.com',
             'dave@example.com',
             ])
        ant_owners = ant.get_roster(MemberRole.owner)
        self.assertEqual(
            [address.email for address in ant_owners.addresses],
            ['anne_0@example.com'])
        bee_owners = bee.get_roster(MemberRole.owner)
        self.assertEqual(
            [address.email for address in bee_owners.addresses],
            ['anne_1@example.com'])

    def test_unsubscribe_members_with_duplicates(self):
        ant = create_list('ant@example.com')
        ant.admin_immed_notify = False
        anne = self._user_manager.create_user('anne@example.com')
        set_preferred(anne)
        ant.subscribe(anne, MemberRole.member)
        # Now we try to unsubscribe Anne twice in the same call.  That's okay
        # because duplicates are ignored.
        success, fail = self._service.unsubscribe_members(
            ant.list_id, [
                'anne@example.com',
                'anne@example.com',
                ])
        self.assertEqual(success, set(['anne@example.com']))
        self.assertEqual(fail, set())

    def test_unsubscribe_members_with_duplicate_failures(self):
        ant = create_list('ant@example.com')
        ant.admin_immed_notify = False
        anne = self._user_manager.create_user('anne@example.com')
        set_preferred(anne)
        ant.subscribe(anne, MemberRole.member)
        # Now we try to unsubscribe a nonmember twice in the same call.
        # That's okay because duplicates are ignored.
        success, fail = self._service.unsubscribe_members(
            ant.list_id, [
                'bart@example.com',
                'bart@example.com',
                ])
        self.assertEqual(success, set())
        self.assertEqual(fail, set(['bart@example.com']))

    def test_find_members_issue_227(self):
        # A user is subscribed to a list with their preferred address.  They
        # have a different secondary linked address which is not subscribed.
        # ISubscriptionService.find_members() should find the first, but not
        # the second 'subscriber'.
        #
        # https://gitlab.com/mailman/mailman/issues/227
        anne = self._user_manager.create_user('anne@example.com')
        set_preferred(anne)
        # Create a secondary address.
        address = self._user_manager.create_address('aperson@example.com')
        address.user = anne
        # Subscribe Anne's user record.
        self._mlist.subscribe(anne)
        # Each of these searches should return only a single member, the one
        # that has Anne's user record as its subscriber.
        call_arguments = [
            # Search by mailing list id.
            dict(list_id=self._mlist.list_id),
            # Search by user id.
            dict(subscriber=anne.user_id),
            # Search by Anne's preferred address.
            dict(subscriber='anne@example.com'),
            # Fuzzy search by address.
            dict(subscriber='anne*'),
            ]
        for arguments in call_arguments:
            members = self._service.find_members(**arguments)
            # We check the lengths twice to ensure that the two "views" of the
            # results match expectations.  len() implicitly calls the query's
            # .count() method which according to the SQLAlchemy documentation
            # does *not* de-duplicate the rows.  In the second case, we turn
            # the result set into a concrete list, which works by iterating
            # over the result.  In both cases, we expect only a single match.
            self.assertEqual(len(members), 1)
            self.assertEqual(len(list(members)), 1)
            self.assertEqual(members[0].user, anne)

    def test_find_members_user_and_secondary_address(self):
        # A user has two subscriptions: the user itself and one of its
        # secondary addresses.
        anne = self._user_manager.create_user('anne@example.com')
        set_preferred(anne)
        # Create a secondary address.
        address = self._user_manager.create_address('aperson@example.com')
        address.user = anne
        # Subscribe the user and the secondary address.
        self._mlist.subscribe(anne)
        self._mlist.subscribe(address)
        # Search for the user-based subscription.
        members = self._service.find_members('anne@example.com')
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]._user, anne)
        # The address-id is None because the user is the subscriber.
        self.assertIsNone(members[0].address_id)
        # Search for the address-based subscription.
        members = self._service.find_members('aperson@example.com')
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]._address, address)
        # The user-id is None because the address is the subscriber.
        self.assertIsNone(members[0].user_id)
        # Search by user-id.  In this case because the address is linked to
        # the user, we should get two results.
        members = self._service.find_members(anne.user_id)
        self.assertEqual(len(members), 2)

    def test_find_members_user_and_primary_address(self):
        # A user has two subscriptions: 1) where the user itself is the
        # subscriber, 2) the address which happens to be the user's preferred
        # address is the subscriber.  Remember that in the model, this
        # represents two separate subscriptions because the user can always
        # change their preferred address.
        anne = self._user_manager.create_user('anne@example.com')
        set_preferred(anne)
        # Subscribe the user and their preferred address.
        self._mlist.subscribe(anne)
        self._mlist.subscribe(anne.preferred_address)
        # Search for the user's address.
        members = self._service.find_members('anne@example.com')
        self.assertEqual(len(members), 2)
        # Search for the user.
        members = self._service.find_members(anne.user_id)
        self.assertEqual(len(members), 2)
