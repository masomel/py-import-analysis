# Copyright (C) 2001-2017 by the Free Software Foundation, Inc.
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

"""Calculate the list owner recipients (includes moderators)."""

from mailman.config import config
from mailman.core.i18n import _
from mailman.interfaces.handler import IHandler
from mailman.interfaces.member import DeliveryStatus
from public import public
from zope.interface import implementer


@public
@implementer(IHandler)
class OwnerRecipients:
    """Calculate the owner (and moderator) recipients for -owner postings."""

    name = 'owner-recipients'
    description = _('Calculate the owner and moderator recipients.')

    def process(self, mlist, msg, msgdata):
        """See `IHandler`."""
        # Short circuit if we've already calculated the recipients list,
        # regardless of whether the list is empty or not.
        if 'recipients' in msgdata:
            return
        # -owner messages go to both the owners and moderators, which is most
        # conveniently accessed via the administrators roster.
        recipients = set(admin.address.email
                         for admin in mlist.administrators.members
                         if admin.delivery_status == DeliveryStatus.enabled)
        # To prevent -owner messages from going into a black hole, if there
        # are no administrators available, the message goes to the site owner.
        if len(recipients) == 0:
            # Ensure that the site owner address is a unicode.
            # See LP: #1130957
            site_owner = config.mailman.site_owner
            if isinstance(site_owner, bytes):
                site_owner = site_owner.decode('utf-8')
            msgdata['recipients'] = set((site_owner,))
        else:
            msgdata['recipients'] = recipients
        # Don't decorate these messages with the header/footers.  Eventually
        # we should support unique decorations for owner emails.
        msgdata['nodecorate'] = True
        # We should probably always VERP deliveries to the owners.  We
        # *really* want to know if they are bouncing.
        msgdata['verp'] = True
