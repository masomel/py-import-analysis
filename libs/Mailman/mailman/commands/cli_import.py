# Copyright (C) 2010-2017 by the Free Software Foundation, Inc.
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

"""Importing list data into Mailman 3."""

import sys
import pickle

from contextlib import ExitStack, contextmanager
from mailman.core.i18n import _
from mailman.database.transaction import transactional
from mailman.interfaces.command import ICLISubCommand
from mailman.interfaces.listmanager import IListManager
from mailman.utilities.importer import Import21Error, import_config_pck
from public import public
from zope.component import getUtility
from zope.interface import implementer


# A fake Bouncer class from Mailman 2.1, we don't use it but there are
# instances in the .pck files.
class Bouncer:
    class _BounceInfo:
        pass


@contextmanager
def hacked_sys_modules():
    assert 'Mailman.Bouncer' not in sys.modules
    sys.modules['Mailman.Bouncer'] = Bouncer
    try:
        yield
    finally:
        del sys.modules['Mailman.Bouncer']


@public
@implementer(ICLISubCommand)
class Import21:
    """Import Mailman 2.1 list data."""

    name = 'import21'

    def add(self, parser, command_parser):
        """See `ICLISubCommand`."""
        self.parser = parser
        # Required positional arguments.
        command_parser.add_argument(
            'listname', metavar='LISTNAME', nargs=1,
            help=_("""\
            The 'fully qualified list name', i.e. the posting address of the
            mailing list to inject the message into."""))
        command_parser.add_argument(
            'pickle_file', metavar='FILENAME', nargs=1,
            help=_('The path to the config.pck file to import.'))

    @transactional
    def process(self, args):
        """See `ICLISubCommand`."""
        # Could be None or sequence of length 0.
        if args.listname is None:
            self.parser.error(_('List name is required'))
            return
        assert len(args.listname) == 1, (
            'Unexpected positional arguments: %s' % args.listname)
        fqdn_listname = args.listname[0]
        mlist = getUtility(IListManager).get(fqdn_listname)
        if mlist is None:
            self.parser.error(_('No such list: $fqdn_listname'))
            return
        if args.pickle_file is None:
            self.parser.error(_('config.pck file is required'))
            return
        assert len(args.pickle_file) == 1, (
            'Unexpected positional arguments: %s' % args.pickle_file)
        filename = args.pickle_file[0]
        with ExitStack() as resources:
            fp = resources.enter_context(open(filename, 'rb'))
            resources.enter_context(hacked_sys_modules())
            while True:
                try:
                    config_dict = pickle.load(
                        fp, encoding='utf-8', errors='ignore')
                except EOFError:
                    break
                except pickle.UnpicklingError:
                    self.parser.error(
                        _('Not a Mailman 2.1 configuration file: $filename'))
                    return
                else:
                    if not isinstance(config_dict, dict):
                        print(_('Ignoring non-dictionary: {0!r}').format(
                            config_dict), file=sys.stderr)
                        continue
                    try:
                        import_config_pck(mlist, config_dict)
                    except Import21Error as error:
                        print(error, file=sys.stderr)
                        sys.exit(1)
