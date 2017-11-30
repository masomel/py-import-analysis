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

"""Interfaces for the pending database.

The pending database contains events that must be confirmed by the user.  It
maps these events to a unique hash that can be used as a token for end user
confirmation.
"""

from public import public
from zope.interface import Attribute, Interface


@public
class IPendable(Interface):
    """A pendable object."""

    PEND_TYPE = Attribute(
        """The type of this pendable.

        Subclasses must define this attribute, and it must be a unique string;
        it's used to efficiently search for all pendables of the given type.
        The PEND_TYPE "type" is reserved.
        """)

    def keys():
        """The keys of the pending event data, all of which are strings."""

    def values():
        """The values of the pending event data, all of which are strings."""

    def items():
        """The key/value pairs of the pending event data.

        Both the keys and values must be strings.
        """


@public
class IPended(Interface):
    """A pended event, tied to a token."""

    token = Attribute("""The pended token.""")

    expiration_date = Attribute("""The expiration date of the pended event.""")


@public
class IPendedKeyValue(Interface):
    """A pended key/value pair."""

    key = Attribute("""The pended key.""")

    value = Attribute("""The pended value.""")


@public
class IPendings(Interface):
    """Interface to pending database."""

    def add(pendable, lifetime=None):
        """Create a new entry in the pending database, returning a token.

        :param pendable: The IPendable instance to add.
        :param lifetime: The amount of time, as a `datetime.timedelta` that
            the pended item should remain in the database.  When None is
            given, a system default maximum lifetime is used.
        :return: A token string for inclusion in urls and email confirmations.
        """

    def confirm(token, *, expunge=True):
        """Return the IPendable matching the token.

        :param token: The token string for the IPendable given by the `.add()`
            method, or None if there is no record associated with the token.
        :param expunge: A flag indicating whether the pendable record should
            also be removed from the database or not.
        :return: The matching IPendable or None if no match was found.
        """

    def evict():
        """Remove all pended items whose lifetime has expired."""

    def find(mlist=None, pend_type=None, confirm=True):
        """Search for the pendables matching the given criteria.

        :param mlist: The mailing list object that the pendables must be
            related to, or None.  The default returns all pendables regardless
            of which mailing list they are related to.
        :type mlist: IMailingList or None.
        :param pend_type: The type of the pendables that are looked for, or
            None.  This corresponds to the `PEND_TYPE` attribute.  The default
            returns all pending types.
        :param confirm: A flag indicating whether the found pendings should be
            "confirmed" or not.  See ``confirm()`` for details.
        :return: An iterator over 2-tuples of the form (token, pendable).
            When ``confirm`` is False, ``pendable`` is None.
        """

    def __iter__():
        """An iterator over all pendables.

        Each element is a 2-tuple of the form (token, dict).
        """

    count = Attribute('The number of pendables in the pendings database.')
