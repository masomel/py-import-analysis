# Copyright (C) 2002-2017 by the Free Software Foundation, Inc.
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

"""The email command 'echo'."""

from mailman.core.i18n import _
from mailman.interfaces.command import ContinueProcessing, IEmailCommand
from public import public
from zope.interface import implementer


SPACE = ' '


@public
@implementer(IEmailCommand)
class Echo:
    """The email 'echo' command."""

    name = 'echo'
    argument_description = '[args]'
    description = _('Echo back your arguments.')
    short_description = description

    def process(self, mlist, msg, msgdata, arguments, results):
        """See `IEmailCommand`."""
        print('echo', SPACE.join(arguments), file=results)
        return ContinueProcessing.yes
