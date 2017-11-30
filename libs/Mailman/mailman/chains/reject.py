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

"""The terminal 'reject' chain."""

import logging

from mailman.app.bounces import bounce_message
from mailman.chains.base import TerminalChainBase
from mailman.core.i18n import _
from mailman.interfaces.chain import RejectEvent
from mailman.interfaces.pipeline import RejectMessage
from public import public
from zope.event import notify


log = logging.getLogger('mailman.vette')

NEWLINE = '\n'
SEMISPACE = '; '


@public
class RejectChain(TerminalChainBase):
    """Reject/bounce a message."""

    name = 'reject'
    description = _('Reject/bounce a message and stop processing.')

    def _process(self, mlist, msg, msgdata):
        """See `TerminalChainBase`."""
        # Start by decorating the message with a header that contains a list
        # of all the rules that matched.  These metadata could be None or an
        # empty list.
        rule_hits = msgdata.get('rule_hits')
        if rule_hits:
            msg['X-Mailman-Rule-Hits'] = SEMISPACE.join(rule_hits)
        rule_misses = msgdata.get('rule_misses')
        if rule_misses:
            msg['X-Mailman-Rule-Misses'] = SEMISPACE.join(rule_misses)
        reasons = msgdata.get('moderation_reasons')
        if reasons is None:
            error = None
        else:
            error = RejectMessage(_("""
Your message to the {list_name} mailing-list was rejected for the following
reasons:

{reasons}

The original message as received by Mailman is attached.
""").format(
    list_name=mlist.display_name,                   # noqa: E122
    reasons=NEWLINE.join(reasons)
    ))
        bounce_message(mlist, msg, error)
        log.info('REJECT: %s', msg.get('message-id', 'n/a'))
        notify(RejectEvent(mlist, msg, msgdata, self))
