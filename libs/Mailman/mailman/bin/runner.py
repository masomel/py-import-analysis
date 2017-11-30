# Copyright (C) 2001-2017 by the Free Software Foundation, Inc.
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

"""The runner process."""

import os
import sys
import signal
import logging
import argparse
import traceback

from mailman.config import config
from mailman.core.i18n import _
from mailman.core.initialize import initialize
from mailman.utilities.modules import find_name
from mailman.version import MAILMAN_VERSION_FULL
from public import public


log = None


# Enable coverage if run under the appropriate test suite.
if os.environ.get('COVERAGE_PROCESS_START') is not None:
    import coverage
    coverage.process_startup()


class ROptionAction(argparse.Action):
    """Callback for -r/--runner option."""
    def __call__(self, parser, namespace, values, option_string=None):
        parts = values.split(':')
        if len(parts) == 1:
            runner = parts[0]
            rslice = rrange = 1
        elif len(parts) == 3:
            runner = parts[0]
            try:
                rslice = int(parts[1])
                rrange = int(parts[2])
            except ValueError:
                parser.error(_('Bad runner specification: $value'))
        else:
            parser.error(_('Bad runner specification: $value'))
        setattr(namespace, self.dest, (runner, rslice, rrange))


def make_runner(name, slice, range, once=False):
    # Several conventions for specifying the runner name are supported.  It
    # could be one of the shortcut names.  If the name is a full module path,
    # use it explicitly.  If the name starts with a dot, it's a class name
    # relative to the Mailman.runner package.
    runner_config = getattr(config, 'runner.' + name, None)
    if runner_config is not None:
        # It was a shortcut name.
        class_path = runner_config['class']
    elif name.startswith('.'):
        class_path = 'mailman.runners' + name
    else:
        class_path = name
    try:
        runner_class = find_name(class_path)
    except ImportError:
        if os.environ.get('MAILMAN_UNDER_MASTER_CONTROL') is not None:
            # Exit with SIGTERM exit code so the master watcher won't try to
            # restart us.
            print(_('Cannot import runner module: $class_path'),
                  file=sys.stderr)
            traceback.print_exc()
            sys.exit(signal.SIGTERM)
        else:
            raise
    if once:
        # Subclass to hack in the setting of the stop flag in _do_periodic()
        class Once(runner_class):
            def _do_periodic(self):
                self.stop()
        return Once(name, slice)
    return runner_class(name, slice)


@public
def main():
    global log

    parser = argparse.ArgumentParser(
        description=_("""\
        Start a runner

        The runner named on the command line is started, and it can either run
        through its main loop once (for those runners that support this) or
        continuously.  The latter is how the master runner starts all its
        subprocesses.

        -r is required unless -l or -h is given, and its argument must be one
        of the names displayed by the -l switch.

        Normally, this script should be started from 'mailman start'.  Running
        it separately or with -o is generally useful only for debugging.  When
        run this way, the environment variable $MAILMAN_UNDER_MASTER_CONTROL
        will be set which subtly changes some error handling behavior.
        """))
    parser.add_argument(
        '--version',
        action='version', version=MAILMAN_VERSION_FULL,
        help=_('Print this version string and exit'))
    parser.add_argument(
        '-C', '--config',
        help=_("""\
        Configuration file to use.  If not given, the environment variable
        MAILMAN_CONFIG_FILE is consulted and used if set.  If neither are
        given, a default configuration file is loaded."""))
    parser.add_argument(
        '-r', '--runner',
        metavar='runner[:slice:range]', dest='runner',
        action=ROptionAction, default=None,
        help=_("""\
        Start the named runner, which must be one of the strings
        returned by the -l option.

        For runners that manage a queue directory, optional
        `slice:range` if given is used to assign multiple runner
        processes to that queue.  range is the total number of runners
        for the queue while slice is the number of this runner from
        [0..range).  For runners that do not manage a queue, slice and
        range are ignored.

        When using the `slice:range` form, you must ensure that each
        runner for the queue is given the same range value.  If
        `slice:runner` is not given, then 1:1 is used.
        """))
    parser.add_argument(
        '-o', '--once',
        default=False, action='store_true', help=_("""\
        Run the named runner exactly once through its main loop.
        Otherwise, the runner runs indefinitely until the process
        receives a signal.  This is not compatible with runners that
        cannot be run once."""))
    parser.add_argument(
        '-l', '--list',
        default=False, action='store_true',
        help=_('List the available runner names and exit.'))
    parser.add_argument(
        '-v', '--verbose',
        default=None, action='store_true', help=_("""\
        Display more debugging information to the log file."""))

    args = parser.parse_args()
    if args.runner is None and not args.list:
        parser.error(_('No runner name given.'))

    # Initialize the system.  Honor the -C flag if given.
    config_path = (None if args.config is None
                   else os.path.abspath(os.path.expanduser(args.config)))
    initialize(config_path, args.verbose)
    log = logging.getLogger('mailman.runner')
    if args.verbose:
        console = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(config.logging.root.format,
                                      config.logging.root.datefmt)
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list:
        descriptions = {}
        for section in config.runner_configs:
            ignore, dot, shortname = section.name.rpartition('.')
            ignore, dot, classname = getattr(section, 'class').rpartition('.')
            descriptions[shortname] = classname
        longest = max(len(name) for name in descriptions)
        for shortname in sorted(descriptions):
            classname = descriptions[shortname]
            spaces = longest - len(shortname)
            name = (' ' * spaces) + shortname       # noqa: F841
            print(_('$name runs $classname'))
        sys.exit(0)

    runner = make_runner(*args.runner, once=args.once)
    runner.set_signals()
    # Now start up the main loop
    log.info('%s runner started.', runner.name)
    runner.run()
    log.info('%s runner exiting.', runner.name)
    sys.exit(runner.status)
