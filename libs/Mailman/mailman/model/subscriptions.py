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

"""Subscription services."""

from mailman.app.membership import delete_member
from mailman.database.transaction import dbconnection
from mailman.interfaces.listmanager import IListManager, NoSuchListError
from mailman.interfaces.member import MemberRole
from mailman.interfaces.subscriptions import (
    ISubscriptionService, TooManyMembersError)
from mailman.interfaces.usermanager import IUserManager
from mailman.model.address import Address
from mailman.model.member import Member
from mailman.model.user import User
from mailman.utilities.queries import QuerySequence
from operator import attrgetter
from public import public
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from zope.component import getUtility
from zope.interface import implementer


@public
@implementer(ISubscriptionService)
class SubscriptionService:
    """Subscription services for the REST API."""

    __name__ = 'members'

    def get_members(self):
        """See `ISubscriptionService`."""
        # {list_id -> {role -> [members]}}
        by_list = {}
        user_manager = getUtility(IUserManager)
        for member in user_manager.members:
            by_role = by_list.setdefault(member.list_id, {})
            members = by_role.setdefault(member.role.name, [])
            members.append(member)
        # Flatten into single list sorted as per the interface.
        all_members = []
        address_of_member = attrgetter('address.email')
        for list_id in sorted(by_list):
            by_role = by_list[list_id]
            all_members.extend(
                sorted(by_role.get('owner', []), key=address_of_member))
            all_members.extend(
                sorted(by_role.get('moderator', []), key=address_of_member))
            all_members.extend(
                sorted(by_role.get('member', []), key=address_of_member))
        return all_members

    @dbconnection
    def get_member(self, store, member_id):
        """See `ISubscriptionService`."""
        members = store.query(Member).filter(Member._member_id == member_id)
        if members.count() == 0:
            return None
        else:
            assert members.count() == 1, 'Too many matching members'
            return members[0]

    @dbconnection
    def _find_members(self, store, subscriber, list_id, role):
        # If `subscriber` is a user id, then we'll search for all addresses
        # which are controlled by the user, otherwise we'll just search for
        # the given address.
        if subscriber is None and list_id is None and role is None:
            return None
        order = (Member.list_id, Address.email, Member.role)
        # Querying for the subscriber is the most complicated part, because
        # the parameter can either be an email address or a user id.  Start by
        # building two queries, one joined on the member's address, and one
        # joined on the member's user.  Add the resulting email address to the
        # selected values to be able to sort on it later on.
        q_address = store.query(Member, Address.email).join(Member._address)
        q_user = store.query(Member, Address.email).join(
            User, User.id == Member.user_id).join(User._preferred_address)
        if subscriber is not None:
            if isinstance(subscriber, str):
                # subscriber is an email address.
                subscriber = subscriber.lower()
                if '*' in subscriber:
                    subscriber = subscriber.replace('*', '%')
                    q_address = q_address.filter(
                        Address.email.like(subscriber))
                    q_user = q_user.filter(Address.email.like(subscriber))
                else:
                    q_address = q_address.filter(Address.email == subscriber)
                    q_user = q_user.filter(Address.email == subscriber)
            else:
                # subscriber is a user id.
                q_address = q_address.join(Address.user).filter(
                    User._user_id == subscriber)
                q_user = q_user.filter(User._user_id == subscriber)
        else:
            # We're not searching for a subscriber so only select preferred
            # addresses (see GL issue 227).
            q_user = q_user.filter(Address.id == User._preferred_address_id)
        # Add additional filters to both queries.
        if list_id is not None:
            q_address = q_address.filter(Member.list_id == list_id)
            q_user = q_user.filter(Member.list_id == list_id)
        if role is not None:
            q_address = q_address.filter(Member.role == role)
            q_user = q_user.filter(Member.role == role)
        # Do a UNION of the two queries, sort the result and generate Members.
        return q_address.union(q_user).order_by(*order).from_self(Member)

    def find_members(self, subscriber=None, list_id=None, role=None):
        """See `ISubscriptionService`."""
        return QuerySequence(self._find_members(subscriber, list_id, role))

    def find_member(self, subscriber=None, list_id=None, role=None):
        """See `ISubscriptionService`."""
        try:
            result = self._find_members(subscriber, list_id, role)
            return (result if result is None else result.one())
        except NoResultFound:
            return None
        except MultipleResultsFound:
            # Coerce the exception into a Mailman-layer exception so call
            # sites don't have to import from SQLAlchemy, resulting in a layer
            # violation.
            raise TooManyMembersError(subscriber, list_id, role)

    def __iter__(self):
        yield from self.get_members()

    def leave(self, list_id, email):
        """See `ISubscriptionService`."""
        mlist = getUtility(IListManager).get_by_list_id(list_id)
        if mlist is None:
            raise NoSuchListError(list_id)
        # XXX for now, no notification or user acknowledgment.
        delete_member(mlist, email, False, False)

    @dbconnection
    def unsubscribe_members(self, store, list_id, emails):
        """See 'ISubscriptionService'."""
        success = set()
        fail = set()
        mlist = getUtility(IListManager).get_by_list_id(list_id)
        if mlist is None:
            raise NoSuchListError(list_id)
        # Start with a query on the matching list-id and role.
        q_member = store.query(Member).filter(
            Member.list_id == list_id,
            Member.role == MemberRole.member)
        # De-duplicate.
        for email in set(emails):
            unsubscribed = False
            # Join with a queries matching the email address and preferred
            # address of any subscribed user.
            q_address = q_member.join(Member._address).filter(
                Address.email == email)
            q_user = q_member.join(Member._user).join(
                User._preferred_address).filter(Address.email == email)
            members = q_address.union(q_user).all()
            for member in members:
                member.unsubscribe()
                unsubscribed = True
            (success if unsubscribed else fail).add(email)
        return success, fail
