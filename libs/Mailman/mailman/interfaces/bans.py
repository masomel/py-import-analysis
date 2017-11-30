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

"""Manager of email address bans."""

from public import public
from zope.interface import Attribute, Interface


@public
class IBan(Interface):
    """A specific ban.

    In general, this interface isn't used publicly.  Instead, bans are managed
    through the `IBanManager` interface.
    """

    email = Attribute('The banned email address, or pattern.')

    list_id = Attribute(
        """The list-id of the mailing list the ban applies to.

        Use ``None`` if this is a global ban.
        """)


@public
class IBanManager(Interface):
    """The global manager of email address bans.

        To manage bans for a specific mailing list, adapt that `IMailingList`
        to an `IBanManager`.  To manage global bans, adapt ``None``.
        """

    bans = Attribute(
        """A `QuerySequence` over all the banned emails.""")

    def ban(email):
        """Ban an email address from subscribing to a mailing list.

        When an email address is banned, it will not be allowed to subscribe
        to the mailing list.  This does not affect any email address that may
        already be subscribed to a mailing list.

        It is also possible to add a 'ban pattern' whereby all email addresses
        matching a Python regular expression can be banned.  This is
        accomplished by using a `^` as the first character in `email`.

        When an email address is already banned.  However, it is possible to
        extend a ban for a specific mailing list into a global ban; both bans
        would be in place and they can be removed individually.

        :param email: The text email address being banned or, if the string
            starts with a caret (^), the email address pattern to ban.
        :type email: str
        """

    def unban(email):
        """Remove an email address ban.

        This removes a specific or global email address ban, which would have
        been added with the `ban()` method.  If a ban is lifted which did not
        exist, this method does nothing.

        :param email: The text email address being unbanned or, if the string
            starts with a caret (^), the email address pattern to unban.
        :type email: str
        """

    def is_banned(email):
        """Check whether a specific email address is banned.

        `email` must be a text email address; it cannot be a pattern.  The
        given email address is checked against all registered bans, both
        specific and regular expression, both for the named mailing list (if
        given), and globally.

        :param email: The text email address being checked.
        :type email: str
        :return: A flag indicating whether the given email address is banned
            or not.
        :rtype: bool
        """

    def __iter__():
        """An iterator over all the banned email addresses.

        :return: iterator over `IBan`"""
