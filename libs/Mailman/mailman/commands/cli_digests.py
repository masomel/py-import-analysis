# Copyright (C) 2015-2017 by the Free Software Foundation, Inc.
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

"""The `send_digests` subcommand."""

import sys

from mailman.app.digests import (
    bump_digest_number_and_volume, maybe_send_digest_now)
from mailman.core.i18n import _
from mailman.interfaces.command import ICLISubCommand
from mailman.interfaces.listmanager import IListManager
from public import public
from zope.component import getUtility
from zope.interface import implementer


@public
@implementer(ICLISubCommand)
class Digests:
    """Operate on digests."""

    name = 'digests'

    def add(self, parser, command_parser):
        """See `ICLISubCommand`."""

        command_parser.add_argument(
            '-l', '--list',
            default=[], dest='lists', metavar='list', action='append',
            help=_("""Operate on this mailing list.  Multiple --list
                   options can be given.  The argument can either be a List-ID
                   or a fully qualified list name.  Without this option,
                   operate on the digests for all mailing lists."""))
        command_parser.add_argument(
            '-s', '--send',
            default=False, action='store_true',
            help=_("""Send any collected digests right now, even if the size
                   threshold has not yet been met."""))
        command_parser.add_argument(
            '-b', '--bump',
            default=False, action='store_true',
            help=_("""Increment the digest volume number and reset the digest
                   number to one.  If given with --send, the volume number is
                   incremented before any current digests are sent."""))
        command_parser.add_argument(
            '-n', '--dry-run',
            default=False, action='store_true',
            help=_("""Don't actually do anything, but in conjunction with
                   --verbose, show what would happen."""))
        command_parser.add_argument(
            '-v', '--verbose',
            default=False, action='store_true',
            help=_("""Print some additional status."""))

    def process(self, args):
        """See `ICLISubCommand`."""
        list_manager = getUtility(IListManager)
        if args.lists:
            lists = []
            for spec in args.lists:
                # We'll accept list-ids or fqdn list names.
                if '@' in spec:
                    mlist = list_manager.get(spec)
                else:
                    mlist = list_manager.get_by_list_id(spec)
                if mlist is None:
                    print(_('No such list found: $spec'), file=sys.stderr)
                else:
                    lists.append(mlist)
        else:
            lists = list(list_manager.mailing_lists)
        if args.bump:
            for mlist in lists:
                if args.verbose:
                    print(_('\
$mlist.list_id is at volume $mlist.volume, number \
${mlist.next_digest_number}'))
                if not args.dry_run:
                    bump_digest_number_and_volume(mlist)
                    if args.verbose:
                        print(_('\
$mlist.list_id bumped to volume $mlist.volume, number \
${mlist.next_digest_number}'))
        if args.send:
            for mlist in lists:
                if args.verbose:
                    print(_('\
$mlist.list_id sent volume $mlist.volume, number ${mlist.next_digest_number}'))
                if not args.dry_run:
                    maybe_send_digest_now(mlist, force=True)
