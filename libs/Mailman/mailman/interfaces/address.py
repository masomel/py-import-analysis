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

"""Interface for email address related information."""

from mailman.interfaces.errors import MailmanError
from public import public
from zope.interface import Attribute, Interface


@public
class EmailError(MailmanError):
    """A generic text email address-related error occurred."""

    def __init__(self, email):
        super().__init__()
        self.email = email

    def __str__(self):
        return self.email


@public
class AddressError(MailmanError):
    """A generic IAddress-related error occurred."""

    def __init__(self, address):
        super().__init__()
        self.address = address

    def __str__(self):
        return str(self.address)


@public
class ExistingAddressError(AddressError):
    """The given email address already exists."""


@public
class AddressAlreadyLinkedError(AddressError):
    """The address is already linked to a user."""


@public
class AddressNotLinkedError(AddressError):
    """The address is not linked to the user."""


@public
class InvalidEmailAddressError(EmailError):
    """Email address is invalid."""


@public
class AddressVerificationEvent:
    """Triggered when an address gets verified or unverified."""

    def __init__(self, address):
        self.address = address

    def __str__(self):
        return '<{} {} {}>'.format(
            self.__class__.__name__,
            self.address.email,
            ('unverified' if self.address.verified_on is None
             else self.address.verified_on))


@public
class IAddress(Interface):
    """Email address related information."""

    email = Attribute(
        """Read-only text email address.""")

    original_email = Attribute(
        """Read-only original case-preserved email address.

        For almost all intents and purposes, email addresses in Mailman are
        case insensitive, however because RFC 2821 allows for case sensitive
        local parts, Mailman preserves the case of the original email address
        when delivering a message to the user.

        `original_email` will be the same as `email` if the original email
        address was all lower case.  Otherwise `original_email` will be the
        case preserved email address; `email` will always be lower case.
        """)

    display_name = Attribute(
        """Optional display name associated with the email address.""")

    registered_on = Attribute(
        """The date and time at which this email address was registered.

        Registeration is really the date at which this address became known to
        us.  It may have been explicitly registered by a user, or it may have
        been implicitly registered, e.g. by showing up in a nonmember
        posting.""")

    verified_on = Attribute(
        """The date and time at which this email address was validated, or
        None if the email address has not yet been validated.  The specific
        method of validation is not defined here.""")

    preferences = Attribute(
        """This address's preferences.""")


@public
class IEmailValidator(Interface):
    """An email validator."""

    def is_valid(email):
        """Check if an email address if valid.

        :param email: A text email address.
        :type email: str
        :return: A flag indicating whether the email address is okay or not.
        :rtype: bool
        """

    def validate(email):
        """Validate an email address.

        :param email: A text email address.
        :type email: str
        :raise InvalidEmailAddressError: when `email` is deemed invalid.
        """
