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

"""Interface describing the basics of a user."""

from mailman.interfaces.address import AddressError
from public import public
from zope.interface import Attribute, Interface


@public
class UnverifiedAddressError(AddressError):
    """Unverified address cannot be used as a user's preferred address."""


@public
class PasswordChangeEvent:
    """Event which gets triggered when a user changes their password."""

    def __init__(self, user):
        self.user = user

    def __str__(self):
        return '<{} {}>'.format(
            self.__class__.__name__, self.user.display_name)


@public
class IUser(Interface):
    """A basic user."""

    display_name = Attribute(
        """This user's display name.""")

    password = Attribute(
        """This user's password information.""")

    user_id = Attribute(
        """The user's unique, random identifier as a UUID.""")

    created_on = Attribute(
        """The date and time at which this user was created.""")

    addresses = Attribute(
        """An iterator over all the `IAddresses` controlled by this user.""")

    preferred_address = Attribute(
        """The user's preferred `IAddress`.  This must be validated.""")

    memberships = Attribute(
        """A roster of this user's memberships.""")

    is_server_owner = Attribute(
        """Boolean flag indicating whether the user is a server owner.""")

    def register(email, display_name=None):
        """Register the given email address and link it to this user.

        :param email: The text email address to register.
        :type email: str
        :param display_name: The user's display name.  If not given the empty
            string is used.
        :type display_name: str
        :return: The address object linked to the user.  If the associated
            address object already existed (unlinked to a user) then the
            `display_name` parameter is ignored.
        :rtype: `IAddress`
        :raises AddressAlreadyLinkedError: if this `IAddress` is already
            linked to another user.
        """

    def link(address):
        """Link this user to the given IAddress.

        Raises AddressAlreadyLinkedError if this IAddress is already linked to
        another user.
        """

    def unlink(address):
        """Unlink this IAddress from the user.

        Raises AddressNotLinkedError if this address is not linked to this
        user, either because it's not linked to any user or it's linked to
        some other user.
        """

    def controls(email):
        """Determine whether this user controls the given email address.

        :param email: The text email address to register.
        :type email: str
        :return: True if the user controls the given email address.
        :rtype: bool
        """

    preferences = Attribute(
        """This user's preferences.""")

    def absorb(user):
        """Merge the given user to ourself.

        All IAddresses linked to `user` are relinked to ourself.  A
        memberships associated with `user` are changed to be memberships
        with ourself.  See `IPreferences.absorb()`.

        The user's `display_name`, `password`, and `is_server_owner` settings
        are absorbed into ours, but only if ours is unset and the given user's
        values are set.

        After being absorbed, the given user and its preferences are
        deleted.

        It is not an error if `user` is ourself, but it is a no-op.

        :param user: The user to merge into ourself.
        :type user: IUser
        :raises TypeError: if `user` is not a user.
        """
