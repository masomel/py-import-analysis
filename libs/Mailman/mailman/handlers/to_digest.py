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

"""Add the message to the list's current digest."""

import os

from mailman.app.digests import maybe_send_digest_now
from mailman.core.i18n import _
from mailman.interfaces.handler import IHandler
from mailman.utilities.mailbox import Mailbox
from public import public
from zope.interface import implementer


@public
@implementer(IHandler)
class ToDigest:
    """Add the message to the digest, possibly sending it."""

    name = 'to-digest'
    description = _('Add the message to the digest, possibly sending it.')

    def process(self, mlist, msg, msgdata):
        """See `IHandler`."""
        # Short-circuit if digests are not enabled or if this message already
        # is a digest.
        if not mlist.digests_enabled or msgdata.get('isdigest'):
            return
        # Open the mailbox that will be used to collect the current digest.
        mailbox_path = os.path.join(mlist.data_path, 'digest.mmdf')
        # Lock the mailbox and append the message.
        with Mailbox(mailbox_path, create=True) as mbox:
            mbox.add(msg)
        maybe_send_digest_now(mlist)
