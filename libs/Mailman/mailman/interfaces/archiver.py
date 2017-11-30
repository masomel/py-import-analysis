# Copyright (C) 2008-2017 by the Free Software Foundation, Inc.
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

"""Interface for archiving schemes."""

from enum import Enum
from public import public
from zope.interface import Attribute, Interface


@public
class ArchivePolicy(Enum):
    never = 0
    private = 1
    public = 2


@public
class ClobberDate(Enum):
    never = 1
    maybe = 2
    always = 3


@public
class IArchiver(Interface):
    """An interface to the archiver."""

    name = Attribute('The name of this archiver')
    is_enabled = Attribute(
        'A flag indicating whether this archiver is enabled site-wide.')

    def list_url(mlist):
        """Return the url to the top of the list's archive.

        If the archiver is not web-accessible, return None.

        :param mlist: The IMailingList object.
        :returns: The url string or None.
        """

    def permalink(mlist, msg):
        """Return the url to the message in the archive.

        This url points directly to the message in the archive.  This method
        only calculates the url, it does not actually archive the message.

        If the archiver is not web-accessible, return None.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """

    def archive_message(mlist, msg):
        """Send the message to the archiver.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """

    # XXX How to handle attachments?
