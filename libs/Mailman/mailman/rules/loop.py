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

"""Look for a posting loop."""

from mailman.core.i18n import _
from mailman.interfaces.rules import IRule
from public import public
from zope.interface import implementer


@public
@implementer(IRule)
class Loop:
    """Look for a posting loop."""

    name = 'loop'
    description = _('Look for a posting loop.')
    record = True

    def check(self, mlist, msg, msgdata):
        """See `IRule`."""
        # Has this message already been posted to this list?
        list_posts = set(value.strip().lower()
                         for value in msg.get_all('list-post', []))
        return mlist.posting_address in list_posts
