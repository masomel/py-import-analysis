# Copyright (C) 1998-2017 by the Free Software Foundation, Inc.
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

"""Add the message to the archives."""

from mailman.config import config
from mailman.core.i18n import _
from mailman.interfaces.archiver import ArchivePolicy
from mailman.interfaces.handler import IHandler
from public import public
from zope.interface import implementer


@public
@implementer(IHandler)
class ToArchive:
    """Add the message to the archives."""

    name = 'to-archive'
    description = _('Add the message to the archives.')

    def process(self, mlist, msg, msgdata):
        """See `IHandler`."""
        # Short circuits.
        if (msgdata.get('isdigest') or
                mlist.archive_policy is ArchivePolicy.never):
            return
        # Common practice seems to favor "X-No-Archive: yes".  No other value
        # for this header seems to make sense, so we'll just test for it's
        # presence.  I'm keeping "X-Archive: no" for backwards compatibility.
        if 'x-no-archive' in msg or msg.get('x-archive', '').lower() == 'no':
            return
        # Send the message to the archiver queue.
        config.switchboards['archive'].enqueue(msg, msgdata)
