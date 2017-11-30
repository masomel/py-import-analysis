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

"""Interface describing the basics of a member."""

from enum import Enum
from mailman.interfaces.errors import MailmanError
from public import public
from zope.interface import Attribute, Interface


@public
class DeliveryMode(Enum):
    # Regular (i.e. non-digest) delivery
    regular = 1
    # Plain text digest delivery
    plaintext_digests = 2
    # MIME digest delivery
    mime_digests = 3
    # Summary digests
    summary_digests = 4


@public
class DeliveryStatus(Enum):
    # Delivery is enabled
    enabled = 1
    # Delivery was disabled by the user
    by_user = 2
    # Delivery was disabled due to bouncing addresses
    by_bounces = 3
    # Delivery was disabled by an administrator or moderator
    by_moderator = 4
    # Disabled for unknown reasons.
    unknown = 5


@public
class MemberRole(Enum):
    member = 1
    owner = 2
    moderator = 3
    nonmember = 4


@public
class MembershipChangeEvent:
    """Base class for subscription/unsubscription events."""

    def __init__(self, mlist, member):
        self.mlist = mlist
        self.member = member


@public
class SubscriptionEvent(MembershipChangeEvent):
    """Event which gets triggered when a user joins a mailing list."""

    def __str__(self):
        return '{0} joined {1}'.format(self.member.address, self.mlist.list_id)


@public
class UnsubscriptionEvent(MembershipChangeEvent):
    """Event which gets triggered when a user leaves a mailing list.

    One thing to keep in mind: because the IMember is deleted when the
    unsubscription happens, this event actually gets triggered just before the
    member is unsubscribed.
    """

    def __str__(self):
        return '{0} left {1}'.format(self.member.address, self.mlist.list_id)


@public
class MembershipError(MailmanError):
    """Base exception for all membership errors."""


@public
class AlreadySubscribedError(MembershipError):
    """The member is already subscribed to the mailing list with this role."""

    def __init__(self, fqdn_listname, email, role):
        super().__init__()
        self.fqdn_listname = fqdn_listname
        self.email = email
        self.role = role

    def __str__(self):
        return '{0} is already a {1} of mailing list {2}'.format(
            self.email, self.role, self.fqdn_listname)


@public
class MembershipIsBannedError(MembershipError):
    """The address is not allowed to subscribe to the mailing list."""

    def __init__(self, mlist, address):
        super().__init__()
        self._mlist = mlist
        self._address = address

    def __str__(self):
        return '{0} is not allowed to subscribe to {1.fqdn_listname}'.format(
            self._address, self._mlist)


@public
class MissingPreferredAddressError(MembershipError):
    """A user without a preferred address attempted to subscribe."""

    def __init__(self, user):
        super().__init__()
        self._user = user

    def __str__(self):
        return 'User must have a preferred address: {0}'.format(self._user)


@public
class NotAMemberError(MembershipError):
    """The address is not a member of the mailing list."""

    def __init__(self, mlist, address):
        super().__init__()
        self._mlist = mlist
        self._address = address

    def __str__(self):
        return '{0} is not a member of {1.fqdn_listname}'.format(
            self._address, self._mlist)


@public
class IMember(Interface):
    """A member of a mailing list."""

    member_id = Attribute(
        """The member's unique, random identifier as a UUID.""")

    list_id = Attribute(
        """The list id of the mailing list the member is subscribed to.""")

    mailing_list = Attribute(
        """The `IMailingList` that the member is subscribed to.""")

    address = Attribute(
        """The email address that's subscribed to the list.""")

    user = Attribute(
        """The user associated with this member.""")

    subscriber = Attribute(
        """The object representing how this member is subscribed.

        This will be an ``IAddress`` if the user is subscribed via an explicit
        address, otherwise if the the user is subscribed via their preferred
        address, it will be an ``IUser``.
        """)

    display_name = Attribute(
        """The best match of the member's display name.

        This will be `subscriber.display_name` if available, which means it
        will either be the display name of the address or user that's
        subscribed.  If unavailable, and the address is the subscriber, then
        the linked user's display name is given, if available.  When all else
        fails, the empty string is returned.
        """)

    preferences = Attribute(
        """This member's preferences.""")

    role = Attribute(
        """The role of this membership.""")

    moderation_action = Attribute(
        """The moderation action for this member as an `Action`.""")

    def unsubscribe():
        """Unsubscribe (and delete) this member from the mailing list."""

    acknowledge_posts = Attribute(
        """Send an acknowledgment for every posting?

        Unlike going through the preferences, this attribute return the
        preference value based on the following lookup order:

        1. The member
        2. The address
        3. The user
        4. System default
        """)

    preferred_language = Attribute(
        """The preferred language for interacting with a mailing list.

        Unlike going through the preferences, this attribute return the
        preference value based on the following lookup order:

        1. The member
        2. The address
        3. The user
        4. System default
        """)

    receive_list_copy = Attribute(
        """Should an explicit recipient receive a list copy?

        Unlike going through `preferences`, this attribute returns the
        preference value based on the following lookup order:

        1. The member
        2. The address
        3. The user
        4. System default
        """)

    receive_own_postings = Attribute(
        """Should the poster get a list copy of their own messages?

        Unlike going through `preferences`, this attribute returns the
        preference value based on the following lookup order:

        1. The member
        2. The address
        3. The user
        4. System default
        """)

    delivery_mode = Attribute(
        """The preferred delivery mode.

        Unlike going through `preferences`, this attribute returns the
        preference value based on the following lookup order:

        1. The member
        2. The address
        3. The user
        4. System default
        """)

    delivery_status = Attribute(
        """The delivery status.

        Unlike going through `preferences`, this attribute returns the
        preference value based on the following lookup order:

        1. The member
        2. The address
        3. The user
        4. System default

        XXX I'm not sure this is the right place to put this.""")
