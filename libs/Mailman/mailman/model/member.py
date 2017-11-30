# Copyright (C) 2007-2017 by the Free Software Foundation, Inc.
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

"""Model for members."""

from mailman.core.constants import system_preferences
from mailman.database.model import Model
from mailman.database.transaction import dbconnection
from mailman.database.types import Enum, SAUnicode, UUID
from mailman.interfaces.action import Action
from mailman.interfaces.address import IAddress
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.member import (
    IMember, MemberRole, MembershipError, UnsubscriptionEvent)
from mailman.interfaces.user import IUser, UnverifiedAddressError
from mailman.interfaces.usermanager import IUserManager
from mailman.utilities.uid import UIDFactory
from public import public
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from zope.component import getUtility
from zope.event import notify
from zope.interface import implementer


uid_factory = UIDFactory(context='members')


@public
@implementer(IMember)
class Member(Model):
    """See `IMember`."""

    __tablename__ = 'member'

    id = Column(Integer, primary_key=True)
    _member_id = Column(UUID)
    role = Column(Enum(MemberRole), index=True)
    list_id = Column(SAUnicode, index=True)
    moderation_action = Column(Enum(Action))

    address_id = Column(Integer, ForeignKey('address.id'), index=True)
    _address = relationship('Address')
    preferences_id = Column(Integer, ForeignKey('preferences.id'), index=True)
    preferences = relationship('Preferences')
    user_id = Column(Integer, ForeignKey('user.id'), index=True)
    _user = relationship('User')

    def __init__(self, role, list_id, subscriber):
        self._member_id = uid_factory.new()
        self.role = role
        self.list_id = list_id
        if IAddress.providedBy(subscriber):
            self._address = subscriber
            # Look this up dynamically.
            self._user = None
        elif IUser.providedBy(subscriber):
            self._user = subscriber
            # Look this up dynamically.
            self._address = None
        else:
            raise ValueError('subscriber must be a user or address')
        if role in (MemberRole.owner, MemberRole.moderator):
            self.moderation_action = Action.accept
        else:
            assert role in (MemberRole.member, MemberRole.nonmember), (
                'Invalid MemberRole: {}'.format(role))
            self.moderation_action = None

    def __repr__(self):
        return '<Member: {} on {} as {}>'.format(
            self.address, self.mailing_list.fqdn_listname, self.role)

    @property
    def mailing_list(self):
        """See `IMember`."""
        list_manager = getUtility(IListManager)
        return list_manager.get_by_list_id(self.list_id)

    @property
    def member_id(self):
        """See `IMember`."""
        return self._member_id

    @property
    def address(self):
        """See `IMember`."""
        return (self._user.preferred_address
                if self._address is None
                else self._address)

    @address.setter
    def address(self, new_address):
        """See `IMember`."""
        if self._address is None:
            # XXX Either we need a better exception here, or we should allow
            # changing a subscription from preferred address to explicit
            # address (and vice versa via del'ing the .address attribute.
            raise MembershipError('Membership is via preferred address')
        if new_address.verified_on is None:
            # A member cannot change their subscription address to an
            # unverified address.
            raise UnverifiedAddressError('Unverified address')
        user = getUtility(IUserManager).get_user(new_address.email)
        if user is None or user != self.user:
            raise MembershipError('Address is not controlled by user')
        self._address = new_address

    @property
    def user(self):
        """See `IMember`."""
        return (self._user
                if self._address is None
                else getUtility(IUserManager).get_user(self._address.email))

    @property
    def subscriber(self):
        return (self._user if self._address is None else self._address)

    @property
    def display_name(self):
        # Try to find a non-empty display name.  We first look at the directly
        # subscribed record, which will either be the address or the user.
        # That's handled automatically by going through member.subscriber.  If
        # that doesn't give us something useful, try whatever user is linked
        # to the subscriber.
        if self.subscriber.display_name:
            return self.subscriber.display_name
        # If an unlinked address is subscribed tehre will be no .user.
        elif self.user is not None and self.user.display_name:
            return self.user.display_name
        else:
            return ''

    def _lookup(self, preference, default=None):
        pref = getattr(self.preferences, preference)
        if pref is not None:
            return pref
        pref = getattr(self.address.preferences, preference)
        if pref is not None:
            return pref
        if self.address.user:
            pref = getattr(self.address.user.preferences, preference)
            if pref is not None:
                return pref
        if default is None:
            return getattr(system_preferences, preference)
        return default

    @property
    def acknowledge_posts(self):
        """See `IMember`."""
        return self._lookup('acknowledge_posts')

    @property
    def preferred_language(self):
        """See `IMember`."""
        missing = object()
        language = self._lookup('preferred_language', missing)
        return (self.mailing_list.preferred_language
                if language is missing
                else language)

    @property
    def receive_list_copy(self):
        """See `IMember`."""
        return self._lookup('receive_list_copy')

    @property
    def receive_own_postings(self):
        """See `IMember`."""
        return self._lookup('receive_own_postings')

    @property
    def delivery_mode(self):
        """See `IMember`."""
        return self._lookup('delivery_mode')

    @property
    def delivery_status(self):
        """See `IMember`."""
        return self._lookup('delivery_status')

    @dbconnection
    def unsubscribe(self, store):
        """See `IMember`."""
        # Yes, this must get triggered before self is deleted.
        notify(UnsubscriptionEvent(self.mailing_list, self))
        store.delete(self.preferences)
        store.delete(self)
