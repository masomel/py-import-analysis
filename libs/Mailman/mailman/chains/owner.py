# Copyright (C) 2012-2017 by the Free Software Foundation, Inc.
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

"""The standard -owner posting chain."""

import logging

from mailman.chains.base import TerminalChainBase
from mailman.config import config
from mailman.core.i18n import _
from mailman.interfaces.chain import AcceptOwnerEvent
from public import public
from zope.event import notify


log = logging.getLogger('mailman.vette')


@public
class BuiltInOwnerChain(TerminalChainBase):
    """Default built-in -owner address chain."""

    name = 'default-owner-chain'
    description = _('The built-in -owner posting chain.')

    def _process(self, mlist, msg, msgdata):
        # At least for now, everything posted to -owners goes through.
        config.switchboards['pipeline'].enqueue(msg, msgdata)
        log.info('OWNER: %s', msg.get('message-id', 'n/a'))
        notify(AcceptOwnerEvent(mlist, msg, msgdata, self))
