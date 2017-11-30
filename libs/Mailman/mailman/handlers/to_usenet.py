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

"""Move the message to the mail->news queue."""

import logging

from mailman.config import config
from mailman.core.i18n import _
from mailman.interfaces.handler import IHandler
from public import public
from zope.interface import implementer


COMMASPACE = ', '
log = logging.getLogger('mailman.error')


@public
@implementer(IHandler)
class ToUsenet:
    """Move the message to the outgoing news queue."""

    name = 'to-usenet'
    description = _('Move the message to the outgoing news queue.')

    def process(self, mlist, msg, msgdata):
        """See `IHandler`."""
        # Short circuits.
        if (not mlist.gateway_to_news or
                msgdata.get('isdigest') or
                msgdata.get('fromusenet')):
            # Short-circuit.
            return
        # Sanity checks.
        error = []
        if not mlist.linked_newsgroup:
            error.append('no newsgroup')
        if not mlist.nntp_host:
            error.append('no NNTP host')
        if error:
            log.error('NNTP gateway improperly configured: %s',
                      COMMASPACE.join(error))
            return
        # Put the message in the news runner's queue.
        config.switchboards['nntp'].enqueue(msg, msgdata, listid=mlist.list_id)
