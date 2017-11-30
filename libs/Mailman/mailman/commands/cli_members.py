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

"""The 'members' subcommand."""

import sys

from contextlib import ExitStack
from email.utils import formataddr, parseaddr
from mailman.app.membership import add_member
from mailman.core.i18n import _
from mailman.database.transaction import transactional
from mailman.interfaces.command import ICLISubCommand
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.member import (
    AlreadySubscribedError, DeliveryMode, DeliveryStatus, MemberRole)
from mailman.interfaces.subscriptions import RequestRecord
from operator import attrgetter
from public import public
from zope.component import getUtility
from zope.interface import implementer


@public
@implementer(ICLISubCommand)
class Members:
    """Manage list memberships.  With no arguments, list all members."""

    name = 'members'

    def add(self, parser, command_parser):
        """See `ICLISubCommand`."""
        self.parser = parser
        command_parser.add_argument(
            '-a', '--add',
            dest='input_filename', metavar='FILENAME',
            help=_("""\
            Add all member addresses in FILENAME.  FILENAME can be '-' to
            indicate standard input.  Blank lines and lines That start with a
            '#' are ignored.  Without this option, this command displays
            mailing list members."""))
        command_parser.add_argument(
            '-o', '--output',
            dest='output_filename', metavar='FILENAME',
            help=_("""Display output to FILENAME instead of stdout.  FILENAME
            can be '-' to indicate standard output."""))
        command_parser.add_argument(
            '-R', '--role',
            default=None, metavar='ROLE',
            choices=('any', 'owner', 'moderator', 'nonmember', 'member',
                     'administrator'),
            help=_("""Display only members with a given ROLE.  The role may be
                   'any', 'member', 'nonmember', 'owner', 'moderator', or
                   'administrator' (i.e. owners and moderators).  If not
                   given, then delivery members are used. """))
        command_parser.add_argument(
            '-r', '--regular',
            default=None, action='store_true',
            help=_('Display only regular delivery members.'))
        command_parser.add_argument(
            '-d', '--digest',
            default=None, metavar='KIND',
            # BAW 2010-01-23 summary digests are not really supported yet.
            choices=('any', 'plaintext', 'mime'),
            help=_("""Display only digest members of KIND.  'any' means any
            digest type, 'plaintext' means only plain text (RFC 1153) type
            digests, 'mime' means MIME type digests."""))
        command_parser.add_argument(
            '-n', '--nomail',
            default=None, metavar='WHY',
            choices=('enabled', 'any', 'unknown'
                     'byadmin', 'byuser', 'bybounces'),
            help=_("""Display only members with a given delivery
            status. 'enabled' means all members whose delivery is enabled,
            'any' means members whose delivery is disabled for any reason,
            'byuser' means that the member disabled their own delivery,
            'bybounces' means that delivery was disabled by the automated
            bounce processor, 'byadmin' means delivery was disabled by the
            list administrator or moderator, and 'unknown' means that delivery
            was disabled for unknown (legacy) reasons."""))
        # Required positional argument.
        command_parser.add_argument(
            'list', metavar='LIST', nargs=1,
            help=_("""\
            The list to operate on.  This can be the fully qualified list
            name', i.e. the posting address of the mailing list or the
            List-ID."""))
        command_parser.epilog = _(
            """Display a mailing list's members, with filtering along various
            criteria.""")

    def process(self, args):
        """See `ICLISubCommand`."""
        assert len(args.list) == 1, 'Missing mailing list name'
        list_spec = args.list[0]
        list_manager = getUtility(IListManager)
        if '@' in list_spec:
            mlist = list_manager.get(list_spec)
        else:
            mlist = list_manager.get_by_list_id(list_spec)
        if mlist is None:
            self.parser.error(_('No such list: $list_spec'))
        if args.input_filename is None:
            self.display_members(mlist, args)
        else:
            self.add_members(mlist, args)

    def display_members(self, mlist, args):
        """Display the members of a mailing list.

        :param mlist: The mailing list to operate on.
        :type mlist: `IMailingList`
        :param args: The command line arguments.
        :type args: `argparse.Namespace`
        """
        if args.digest == 'any':
            digest_types = [
                DeliveryMode.plaintext_digests,
                DeliveryMode.mime_digests,
                DeliveryMode.summary_digests,
                ]
        elif args.digest is not None:
            digest_types = [DeliveryMode[args.digest + '_digests']]
        else:
            # Don't filter on digest type.
            pass

        if args.nomail is None:
            # Don't filter on delivery status.
            pass
        elif args.nomail == 'byadmin':
            status_types = [DeliveryStatus.by_moderator]
        elif args.nomail.startswith('by'):
            status_types = [DeliveryStatus['by_' + args.nomail[2:]]]
        elif args.nomail == 'enabled':
            status_types = [DeliveryStatus.enabled]
        elif args.nomail == 'unknown':
            status_types = [DeliveryStatus.unknown]
        elif args.nomail == 'any':
            status_types = [
                DeliveryStatus.by_user,
                DeliveryStatus.by_bounces,
                DeliveryStatus.by_moderator,
                DeliveryStatus.unknown,
                ]
        else:
            self.parser.error(_('Unknown delivery status: $args.nomail'))

        if args.role is None:
            # By default, filter on members.
            roster = mlist.members
        elif args.role == 'administrator':
            roster = mlist.administrators
        elif args.role == 'any':
            roster = mlist.subscribers
        else:
            try:
                roster = mlist.get_roster(MemberRole[args.role])
            except KeyError:
                self.parser.error(_('Unknown member role: $args.role'))

        with ExitStack() as resources:
            if args.output_filename == '-' or args.output_filename is None:
                fp = sys.stdout
            else:
                fp = resources.enter_context(
                    open(args.output_filename, 'w', encoding='utf-8'))
            addresses = list(roster.addresses)
            if len(addresses) == 0:
                print(_('$mlist.list_id has no members'), file=fp)
                return
            for address in sorted(addresses, key=attrgetter('email')):
                if args.regular:
                    member = roster.get_member(address.email)
                    if member.delivery_mode != DeliveryMode.regular:
                        continue
                if args.digest is not None:
                    member = roster.get_member(address.email)
                    if member.delivery_mode not in digest_types:
                        continue
                if args.nomail is not None:
                    member = roster.get_member(address.email)
                    if member.delivery_status not in status_types:
                        continue
                print(
                    formataddr((address.display_name, address.original_email)),
                    file=fp)

    @transactional
    def add_members(self, mlist, args):
        """Add the members in a file to a mailing list.

        :param mlist: The mailing list to operate on.
        :type mlist: `IMailingList`
        :param args: The command line arguments.
        :type args: `argparse.Namespace`
        """
        with ExitStack() as resources:
            if args.input_filename == '-':
                fp = sys.stdin
            else:
                fp = resources.enter_context(
                    open(args.input_filename, 'r', encoding='utf-8'))
            for line in fp:
                # Ignore blank lines and lines that start with a '#'.
                if line.startswith('#') or len(line.strip()) == 0:
                    continue
                # Parse the line and ensure that the values are unicodes.
                display_name, email = parseaddr(line)
                try:
                    add_member(mlist,
                               RequestRecord(email, display_name,
                                             DeliveryMode.regular,
                                             mlist.preferred_language.code))
                except AlreadySubscribedError:
                    # It's okay if the address is already subscribed, just
                    # print a warning and continue.
                    if not display_name:
                        print(_('Already subscribed (skipping): $email'))
                    else:
                        print(_('Already subscribed (skipping): '
                                '$display_name <$email>'))
