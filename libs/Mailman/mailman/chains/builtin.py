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

"""The default built-in starting chain."""

import logging

from mailman.chains.base import Link
from mailman.core.i18n import _
from mailman.interfaces.chain import IChain, LinkAction
from public import public
from zope.interface import implementer


log = logging.getLogger('mailman.vette')


@public
@implementer(IChain)
class BuiltInChain:
    """Default built-in chain."""

    name = 'default-posting-chain'
    description = _('The built-in moderation chain.')

    _link_descriptions = (
        # First check DMARC.  For a reject or discard, the rule hits and we
        # jump to the moderation chain to do the action.  Otherwise, the rule
        # misses buts sets msgdata['dmarc'] for the handler.
        ('dmarc-mitigation', LinkAction.jump, 'moderation'),
        ('approved', LinkAction.jump, 'accept'),
        ('emergency', LinkAction.jump, 'hold'),
        ('loop', LinkAction.jump, 'discard'),
        # Discard emails from banned addresses.
        ('banned-address', LinkAction.jump, 'discard'),
        # Determine whether the member or nonmember has an action shortcut.
        ('member-moderation', LinkAction.jump, 'moderation'),
        # Take a detour through the header matching chain.
        ('truth', LinkAction.detour, 'header-match'),
        # Check for nonmember moderation.
        ('nonmember-moderation', LinkAction.jump, 'moderation'),
        # Do all of the following before deciding whether to hold the message.
        ('administrivia', LinkAction.defer, None),
        ('implicit-dest', LinkAction.defer, None),
        ('max-recipients', LinkAction.defer, None),
        ('max-size', LinkAction.defer, None),
        ('news-moderation', LinkAction.defer, None),
        ('no-subject', LinkAction.defer, None),
        ('suspicious-header', LinkAction.defer, None),
        # Now if any of the above hit, jump to the hold chain.
        ('any', LinkAction.jump, 'hold'),
        # Finally, the builtin chain jumps to acceptance.
        ('truth', LinkAction.jump, 'accept'),
        )

    def __init__(self):
        self._cached_links = None

    def get_links(self, mlist, msg, msgdata):
        """See `IChain`."""
        if self._cached_links is None:
            self._cached_links = links = []
            for rule, action, chain in self._link_descriptions:
                links.append(Link(rule, action, chain))
        return iter(self._cached_links)
