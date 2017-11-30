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

"""Test members."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.interfaces.action import Action
from mailman.interfaces.member import MemberRole, MembershipError
from mailman.interfaces.user import UnverifiedAddressError
from mailman.interfaces.usermanager import IUserManager
from mailman.model.member import Member
from mailman.testing.helpers import set_preferred
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import now
from zope.component import getUtility


class TestMember(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._usermanager = getUtility(IUserManager)

    def test_cannot_set_address_with_preferred_address_subscription(self):
        # A user is subscribed to a mailing list with their preferred address.
        # You cannot set the `address` attribute on such IMembers.
        anne = self._usermanager.create_user('anne@example.com')
        set_preferred(anne)
        # Subscribe with the IUser object, not the address.  This makes Anne a
        # member via her preferred address.
        member = self._mlist.subscribe(anne)
        new_address = anne.register('aperson@example.com')
        new_address.verified_on = now()
        self.assertRaises(MembershipError,
                          setattr, member, 'address', new_address)

    def test_cannot_change_to_unverified_address(self):
        # A user is subscribed to a mailing list with an explicit address.
        # You cannot set the `address` attribute to an unverified address.
        anne = self._usermanager.create_user('anne@example.com')
        address = list(anne.addresses)[0]
        member = self._mlist.subscribe(address)
        new_address = anne.register('aperson@example.com')
        # The new address is not verified.
        self.assertRaises(UnverifiedAddressError,
                          setattr, member, 'address', new_address)

    def test_cannot_change_to_address_uncontrolled_address(self):
        # A user tries to change their subscription to an address they do not
        # control.
        anne = self._usermanager.create_user('anne@example.com')
        address = list(anne.addresses)[0]
        member = self._mlist.subscribe(address)
        new_address = self._usermanager.create_address('nobody@example.com')
        new_address.verified_on = now()
        # The new address is not verified.
        self.assertRaises(MembershipError,
                          setattr, member, 'address', new_address)

    def test_cannot_change_to_address_controlled_by_other_user(self):
        # A user tries to change their subscription to an address some other
        # user controls.
        anne = self._usermanager.create_user('anne@example.com')
        anne_address = list(anne.addresses)[0]
        bart = self._usermanager.create_user('bart@example.com')
        bart_address = list(bart.addresses)[0]
        bart_address.verified_on = now()
        member = self._mlist.subscribe(anne_address)
        # The new address is not verified.
        self.assertRaises(MembershipError,
                          setattr, member, 'address', bart_address)

    def test_member_ctor_value_error(self):
        # ValueError when passing in anything but a user or address.
        self.assertRaises(ValueError, Member, MemberRole.member,
                          self._mlist.list_id,
                          'aperson@example.com')

    def test_unsubscribe(self):
        address = self._usermanager.create_address('anne@example.com')
        address.verified_on = now()
        self._mlist.subscribe(address)
        self.assertEqual(len(list(self._mlist.members.members)), 1)
        member = self._mlist.members.get_member('anne@example.com')
        member.unsubscribe()
        self.assertEqual(len(list(self._mlist.members.members)), 0)

    def test_default_moderation_action(self):
        # Owners and moderators have their posts accepted, members and
        # nonmembers default to the mailing list's action for their type.
        anne = self._usermanager.create_user('anne@example.com')
        bart = self._usermanager.create_user('bart@example.com')
        cris = self._usermanager.create_user('cris@example.com')
        dana = self._usermanager.create_user('dana@example.com')
        set_preferred(anne)
        set_preferred(bart)
        set_preferred(cris)
        set_preferred(dana)
        anne_member = self._mlist.subscribe(anne, MemberRole.owner)
        bart_member = self._mlist.subscribe(bart, MemberRole.moderator)
        cris_member = self._mlist.subscribe(cris, MemberRole.member)
        dana_member = self._mlist.subscribe(dana, MemberRole.nonmember)
        self.assertEqual(anne_member.moderation_action, Action.accept)
        self.assertEqual(bart_member.moderation_action, Action.accept)
        self.assertIsNone(cris_member.moderation_action)
        self.assertIsNone(dana_member.moderation_action)
