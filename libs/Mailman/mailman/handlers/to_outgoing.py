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

"""Re-queue the message to the outgoing queue.

This module is only for use by the IncomingRunner for delivering messages
posted to the list membership.  Anything else that needs to go out to some
recipient should just be placed in the out queue directly.
"""

from mailman.config import config
from mailman.core.i18n import _
from mailman.interfaces.handler import IHandler
from public import public
from zope.interface import implementer


@public
@implementer(IHandler)
class ToOutgoing:
    """Send the message to the outgoing queue."""

    name = 'to-outgoing'
    description = _('Send the message to the outgoing queue.')

    def process(self, mlist, msg, msgdata):
        """See `IHandler`."""
        config.switchboards['out'].enqueue(msg, msgdata, listid=mlist.list_id)
