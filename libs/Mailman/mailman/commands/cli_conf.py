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

"""Print the mailman configuration."""

import sys

from contextlib import closing
from lazr.config._config import Section
from mailman.config import config
from mailman.core.i18n import _
from mailman.interfaces.command import ICLISubCommand
from public import public
from zope.interface import implementer


@public
@implementer(ICLISubCommand)
class Conf:
    """Print the mailman configuration."""

    name = 'conf'

    def add(self, parser, command_parser):
        """See `ICLISubCommand`."""

        self.parser = parser
        command_parser.add_argument(
            '-o', '--output',
            action='store', help=_("""\
            File to send the output to.  If not given, or if '-' is given,
            standard output is used."""))
        command_parser.add_argument(
            '-s', '--section',
            action='store', help=_("""\
            Section to use for the lookup.  If no key is given, all the
            key-value pairs of the given section will be displayed.
            """))
        command_parser.add_argument(
            '-k', '--key',
            action='store', help=_("""\
            Key to use for the lookup.  If no section is given, all the
            key-values pair from any section matching the given key will be
            displayed.
            """))

    def _get_value(self, section, key):
        return getattr(getattr(config, section), key)

    def _sections(self):
        return sorted(config.schema._section_schemas)

    def _print_full_syntax(self, section, key, value, output):
        print('[{}] {}: {}'.format(section, key, value), file=output)

    def _show_key_error(self, section, key):
        self.parser.error('Section {}: No such key: {}'.format(section, key))

    def _show_section_error(self, section):
        self.parser.error('No such section: {}'.format(section))

    def _print_values_for_section(self, section, output):
        current_section = sorted(getattr(config, section))
        for key in current_section:
            self._print_full_syntax(section, key,
                                    self._get_value(section, key), output)

    def _section_exists(self, section):
        # Not all of the attributes in config are actual sections, so we have
        # to check the section's type.
        return (hasattr(config, section) and
                isinstance(getattr(config, section), Section))

    def _inner_process(self, args, output):
        # Process the command, ignoring the closing of the output file.
        section = args.section
        key = args.key
        # Case 1: Both section and key are given, so we can directly look up
        # the value.
        if section is not None and key is not None:
            if not self._section_exists(section):
                self._show_section_error(section)
            elif not hasattr(getattr(config, section), key):
                self._show_key_error(section, key)
            else:
                print(self._get_value(section, key), file=output)
        # Case 2: Section is given, key is not given.
        elif section is not None and key is None:
            if self._section_exists(section):
                self._print_values_for_section(section, output)
            else:
                self._show_section_error(section)
        # Case 3: Section is not given, key is given.
        elif section is None and key is not None:
            for current_section in self._sections():
                # We have to ensure that the current section actually exists
                # and that it contains the given key.
                if (self._section_exists(current_section) and
                        hasattr(getattr(config, current_section), key)):
                    self._print_full_syntax(
                        current_section, key,
                        self._get_value(current_section, key),
                        output)
        # Case 4: Neither section nor key are given, just display all the
        # sections and their corresponding key/value pairs.
        elif section is None and key is None:
            for current_section in self._sections():
                # However, we have to make sure that the current sections and
                # key which are being looked up actually exist before trying
                # to print them.
                if self._section_exists(current_section):
                    self._print_values_for_section(current_section, output)

    def process(self, args):
        """See `ICLISubCommand`."""
        if args.output is None or args.output == '-':
            self._inner_process(args, sys.stdout)
        else:
            with closing(open(args.output, 'w')) as output:
                self._inner_process(args, output)
