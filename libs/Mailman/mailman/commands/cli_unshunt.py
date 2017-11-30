# Copyright (C) 2009-2017 by the Free Software Foundation, Inc.
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

"""The 'unshunt' command."""

import sys

from mailman.config import config
from mailman.core.i18n import _
from mailman.interfaces.command import ICLISubCommand
from public import public
from zope.interface import implementer


@public
@implementer(ICLISubCommand)
class Unshunt:
    """Unshunt messages."""

    name = 'unshunt'

    def add(self, parser, command_parser):
        """See `ICLISubCommand`."""
        self.parser = parser
        command_parser.add_argument(
            '-d', '--discard',
            default=False, action='store_true',
            help=_("""\
            Discard all shunted messages instead of moving them back to their
            original queue."""))

    def process(self, args):
        """See `ICLISubCommand`."""
        shunt_queue = config.switchboards['shunt']
        shunt_queue.recover_backup_files()

        for filebase in shunt_queue.files:
            try:
                msg, msgdata = shunt_queue.dequeue(filebase)
                which_queue = msgdata.get('whichq', 'in')
                if not args.discard:
                    config.switchboards[which_queue].enqueue(msg, msgdata)
            except Exception:
                print(_('Cannot unshunt message $filebase, skipping:\n$error'),
                      file=sys.stderr)
            else:
                # Unlink the .bak file left by dequeue()
                shunt_queue.finish(filebase)
