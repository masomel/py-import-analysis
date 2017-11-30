# Copyright (C) 2013-2017 by the Free Software Foundation, Inc.
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

"""Creation/deletion hooks for the Exim4 MTA."""

from mailman.interfaces.mta import IMailTransportAgentLifecycle
from public import public
from zope.interface import implementer


@public
@implementer(IMailTransportAgentLifecycle)
class LMTP:
    """Connect Mailman to Exim4 via LMTP.

    See `IMailTransportAgentLifecycle`.
    """

    # Exim4 handles all configuration itself, by finding the list config file.
    def __init__(self):
        pass

    def create(self, mlist):
        pass

    delete = create

    def regenerate(self, directory=None):
        """See `IMailTransportAgentLifecycle`."""
        pass
