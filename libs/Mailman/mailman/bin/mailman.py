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

"""The 'mailman' command dispatcher."""

import os
import argparse

from functools import cmp_to_key
from mailman.core.i18n import _
from mailman.core.initialize import initialize
from mailman.database.transaction import transaction
from mailman.interfaces.command import ICLISubCommand
from mailman.utilities.modules import find_components
from mailman.version import MAILMAN_VERSION_FULL
from public import public
from zope.interface.verify import verifyObject


# --help should display the subcommands by alphabetical order, except that
# 'mailman help' should be first.
def _help_sorter(command, other):
    """Sorting helper."""
    if command.name == 'help':
        return -1
    elif other.name == 'help':
        return 1
    elif command.name < other.name:
        return -1
    elif command.name == other.name:
        return 0
    else:
        assert command.name > other.name
        return 1


@public
def main():
    """The `mailman` command dispatcher."""
    # Create the basic parser and add all globally common options.
    parser = argparse.ArgumentParser(
        description=_("""\
        The GNU Mailman mailing list management system
        Copyright 1998-2017 by the Free Software Foundation, Inc.
        http://www.list.org
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        '-v', '--version',
        action='version', version=MAILMAN_VERSION_FULL,
        help=_('Print this version string and exit'))
    parser.add_argument(
        '-C', '--config',
        help=_("""\
        Configuration file to use.  If not given, the environment variable
        MAILMAN_CONFIG_FILE is consulted and used if set.  If neither are
        given, a default configuration file is loaded."""))
    # Look at all modules in the mailman.bin package and if they are prepared
    # to add a subcommand, let them do so.  I'm still undecided as to whether
    # this should be pluggable or not.  If so, then we'll probably have to
    # partially parse the arguments now, then initialize the system, then find
    # the plugins.  Punt on this for now.
    subparser = parser.add_subparsers(title='Commands')
    subcommands = []
    for command_class in find_components('mailman.commands', ICLISubCommand):
        command = command_class()
        verifyObject(ICLISubCommand, command)
        subcommands.append(command)
    subcommands.sort(key=cmp_to_key(_help_sorter))
    for command in subcommands:
        command_parser = subparser.add_parser(
            command.name, help=_(command.__doc__))
        command.add(parser, command_parser)
        command_parser.set_defaults(func=command.process)
    args = parser.parse_args()
    if len(args.__dict__) <= 1:
        # No arguments or subcommands were given.
        parser.print_help()
        parser.exit()
    # Initialize the system.  Honor the -C flag if given.
    config_path = (None if args.config is None
                   else os.path.abspath(os.path.expanduser(args.config)))
    initialize(config_path)
    # Perform the subcommand option.
    with transaction():
        args.func(args)
