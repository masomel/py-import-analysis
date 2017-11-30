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

"""An implementation of an IRoster.

These are hard-coded rosters which know how to filter a set of members to find
the ones that fit a particular role.  These are used as the member, owner,
moderator, and administrator roster filters.
"""

from mailman.database.transaction import dbconnection
from mailman.interfaces.member import DeliveryMode, MemberRole
from mailman.interfaces.roster import IRoster
from mailman.model.address import Address
from mailman.model.member import Member
from public import public
from sqlalchemy import or_
from zope.interface import implementer


@public
@implementer(IRoster)
class AbstractRoster:
    """An abstract IRoster class.

    This class takes the simple approach of implemented the 'users' and
    'addresses' properties in terms of the 'members' property.  This may not
    be the most efficient way, but it works.

    This requires that subclasses implement the 'members' property.
    """
    role = None

    def __init__(self, mlist):
        self._mlist = mlist

    @dbconnection
    def _query(self, store):
        return store.query(Member).filter(
            Member.list_id == self._mlist.list_id,
            Member.role == self.role)

    @property
    def members(self):
        """See `IRoster`."""
        yield from self._query()

    @property
    def member_count(self):
        """See `IRoster`."""
        return self._query().count()

    @property
    def users(self):
        """See `IRoster`."""
        # Members are linked to addresses, which in turn are linked to users.
        # So while the 'members' attribute does most of the work, we have to
        # keep a set of unique users.  It's possible for the same user to be
        # subscribed to a mailing list multiple times with different
        # addresses.
        yield from set(member.address.user for member in self.members)

    @property
    def addresses(self):
        """See `IRoster`."""
        # Every Member is linked to exactly one address so the 'members'
        # attribute does most of the work.
        for member in self.members:
            yield member.address

    @dbconnection
    def _get_all_memberships(self, store, email):
        # Avoid circular imports.
        from mailman.model.user import User
        # Here's a query that finds all members subscribed with an explicit
        # email address.
        members_a = store.query(Member).filter(
            Member.list_id == self._mlist.list_id,
            Member.role == self.role,
            Address.email == email,
            Member.address_id == Address.id)
        # Here's a query that finds all members subscribed with their
        # preferred address.
        members_u = store.query(Member).filter(
            Member.list_id == self._mlist.list_id,
            Member.role == self.role,
            Address.email == email,
            Member.user_id == User.id,
            User._preferred_address_id == Address.id)
        return members_a.union(members_u).all()

    def get_member(self, email):
        """See ``IRoster``."""
        memberships = self._get_all_memberships(email)
        count = len(memberships)
        if count == 0:
            return None
        elif count == 1:
            return memberships[0]
        assert count == 2, 'Unexpected membership count: {}'.format(count)
        # This is the case where the email address is subscribed both
        # explicitly and indirectly through the preferred address.  By
        # definition, we return the explicit address membership only.
        return (memberships[0]
                if memberships[0]._address is not None
                else memberships[1])

    def get_memberships(self, email):
        """See ``IRoster``."""
        memberships = self._get_all_memberships(email)
        count = len(memberships)
        assert 0 <= count <= 2, 'Unexpected membership count: {}'.format(
            count)
        return memberships


@public
class MemberRoster(AbstractRoster):
    """Return all the members of a list."""

    name = 'member'
    role = MemberRole.member


@public
class NonmemberRoster(AbstractRoster):
    """Return all the nonmembers of a list."""

    name = 'nonmember'
    role = MemberRole.nonmember


@public
class OwnerRoster(AbstractRoster):
    """Return all the owners of a list."""

    name = 'owner'
    role = MemberRole.owner


@public
class ModeratorRoster(AbstractRoster):
    """Return all the owners of a list."""

    name = 'moderator'
    role = MemberRole.moderator


@public
class AdministratorRoster(AbstractRoster):
    """Return all the administrators of a list."""

    name = 'administrator'

    @dbconnection
    def _query(self, store):
        return store.query(Member).filter(
            Member.list_id == self._mlist.list_id,
            or_(Member.role == MemberRole.owner,
                Member.role == MemberRole.moderator))

    @dbconnection
    def get_member(self, store, email):
        """See `IRoster`."""
        return store.query(Member).filter(
            Member.list_id == self._mlist.list_id,
            or_(Member.role == MemberRole.moderator,
                Member.role == MemberRole.owner),
            Address.email == email,
            Member.address_id == Address.id).one_or_none()


@public
class DeliveryMemberRoster(AbstractRoster):
    """Return all the members having a particular kind of delivery."""

    role = MemberRole.member

    @property
    def member_count(self):
        """See `IRoster`."""
        # XXX 2012-03-15 BAW: It would be nice to make this more efficient.
        # The problem is that you'd have to change the loop in _get_members()
        # checking the delivery mode to a query parameter.
        return len(tuple(self.members))

    @dbconnection
    def _get_members(self, store, *delivery_modes):
        """The set of members for a mailing list, filter by delivery mode.

        :param delivery_modes: The modes to filter on.
        :type delivery_modes: sequence of `DeliveryMode`.
        :return: A generator of members.
        :rtype: generator
        """
        results = store.query(Member).filter_by(
            list_id=self._mlist.list_id,
            role=MemberRole.member)
        for member in results:
            if member.delivery_mode in delivery_modes:
                yield member


@public
class RegularMemberRoster(DeliveryMemberRoster):
    """Return all the regular delivery members of a list."""

    name = 'regular_members'

    @property
    def members(self):
        """See `IRoster`."""
        yield from self._get_members(DeliveryMode.regular)


@public
class DigestMemberRoster(DeliveryMemberRoster):
    """Return all the regular delivery members of a list."""

    name = 'digest_members'

    @property
    def members(self):
        """See `IRoster`."""
        yield from self._get_members(
            DeliveryMode.plaintext_digests,
            DeliveryMode.mime_digests,
            DeliveryMode.summary_digests)


@public
class Subscribers(AbstractRoster):
    """Return all subscribed members regardless of their role."""

    name = 'subscribers'

    @dbconnection
    def _query(self, store):
        return store.query(Member).filter_by(list_id=self._mlist.list_id)


@public
@implementer(IRoster)
class Memberships:
    """A roster of a single user's memberships."""

    name = 'memberships'

    def __init__(self, user):
        self._user = user

    @dbconnection
    def _query(self, store):
        results = store.query(Member).filter(
            Member.user_id == self._user.id
            ).union(
                store.query(Member).join(Address).filter(
                    Address.user_id == self._user.id)
                )
        return results.distinct()

    @property
    def member_count(self):
        """See `IRoster`."""
        return self._query().count()

    @property
    def members(self):
        """See `IRoster`."""
        yield from self._query()

    @property
    def users(self):
        """See `IRoster`."""
        yield self._user

    @property
    def addresses(self):
        """See `IRoster`."""
        yield from self._user.addresses

    @dbconnection
    def get_member(self, store, email):
        """See `IRoster`."""
        raise NotImplementedError

    @dbconnection
    def get_memberships(self, store, address):
        """See `IRoster`."""
        raise NotImplementedError
