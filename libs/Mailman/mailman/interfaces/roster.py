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

"""Interface for a roster of members."""

from public import public
from zope.interface import Attribute, Interface


@public
class IRoster(Interface):
    """A roster is a collection of `IMembers`."""

    name = Attribute(
        """The name for this roster.

        Rosters are considered equal if they have the same name.""")

    members = Attribute(
        """An iterator over all the IMembers managed by this roster.""")

    member_count = Attribute(
        """The number of members managed by this roster.""")

    users = Attribute(
        """An iterator over all the IUsers reachable by this roster.

        This returns all the users for all the members managed by this roster.
        """)

    addresses = Attribute(
        """An iterator over all the IAddresses reachable by this roster.

        This returns all the addresses for all the users for all the members
        managed by this roster.
        """)

    def get_member(email):
        """Get the member for the given address.

        *Note* that it is possible for an email to be subscribed to a
        mailing list twice, once through its explicit address and once
        indirectly through a user's preferred address.  In this case,
        this API always returns the explicit address.  Use
        ``get_memberships()`` to return them all.

        :param email: The email address to search for.
        :type email: string
        :return: The member if found, otherwise None
        :rtype: `IMember` or None
        """

    def get_memberships(email):
        """Get the memberships for the given address.

        :param email: The email address to search for.
        :type email: string
        :return: All the memberships associated with this email address.
        :rtype: sequence of length 0, 1, or 2 of ``IMember``
        """
