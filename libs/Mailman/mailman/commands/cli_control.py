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

"""Start/stop/reopen/restart commands."""

import os
import sys
import errno
import signal
import logging

from mailman.bin.master import WatcherState, master_state
from mailman.config import config
from mailman.core.i18n import _
from mailman.interfaces.command import ICLISubCommand
from public import public
from zope.interface import implementer


qlog = logging.getLogger('mailman.runner')


@public
@implementer(ICLISubCommand)
class Start:
    """Start the Mailman master and runner processes."""

    name = 'start'

    def add(self, parser, command_parser):
        """See `ICLISubCommand`."""
        self.parser = parser
        command_parser.add_argument(
            '-f', '--force',
            default=False, action='store_true',
            help=_("""\
            If the master watcher finds an existing master lock, it will
            normally exit with an error message.  With this option, the master
            will perform an extra level of checking.  If a process matching
            the host/pid described in the lock file is running, the master
            will still exit, requiring you to manually clean up the lock.  But
            if no matching process is found, the master will remove the
            apparently stale lock and make another attempt to claim the master
            lock."""))
        command_parser.add_argument(
            '-u', '--run-as-user',
            default=True, action='store_false',
            help=_("""\
            Normally, this script will refuse to run if the user id and group
            id are not set to the 'mailman' user and group (as defined when
            you configured Mailman).  If run as root, this script will change
            to this user and group before the check is made.

            This can be inconvenient for testing and debugging purposes, so
            the -u flag means that the step that sets and checks the uid/gid
            is skipped, and the program is run as the current user and group.
            This flag is not recommended for normal production environments.

            Note though, that if you run with -u and are not in the mailman
            group, you may have permission problems, such as being unable to
            delete a list's archives through the web.  Tough luck!"""))
        command_parser.add_argument(
            '-q', '--quiet',
            default=False, action='store_true',
            help=_("""\
            Don't print status messages.  Error messages are still printed to
            standard error."""))

    def process(self, args):
        """See `ICLISubCommand`."""
        # Although there's a potential race condition here, it's a better user
        # experience for the parent process to refuse to start twice, rather
        # than having it try to start the master, which will error exit.
        status, lock = master_state()
        if status is WatcherState.conflict:
            self.parser.error(_('GNU Mailman is already running'))
        elif status in (WatcherState.stale_lock, WatcherState.host_mismatch):
            if args.force is None:
                self.parser.error(
                    _('A previous run of GNU Mailman did not exit '
                      'cleanly.  Try using --force.'))
        def log(message):                                  # noqa: E306
            if not args.quiet:
                print(message)
        # Try to find the path to a valid, existing configuration file, and
        # refuse to start if one cannot be found.
        if args.config is not None:
            config_path = args.config
        elif config.filename is not None:
            config_path = config.filename
        else:
            config_path = os.path.join(config.VAR_DIR, 'etc', 'mailman.cfg')
            if not os.path.exists(config_path):
                print(_("""\
No valid configuration file could be found, so Mailman will refuse to start.
Use -C/--config to specify a valid configuration file."""), file=sys.stderr)
                sys.exit(1)
        # Daemon process startup according to Stevens, Advanced Programming in
        # the UNIX Environment, Chapter 13.
        pid = os.fork()
        if pid:
            # parent
            log(_("Starting Mailman's master runner"))
            return
        # child: Create a new session and become the session leader, but since
        # we won't be opening any terminal devices, don't do the
        # ultra-paranoid suggestion of doing a second fork after the setsid()
        # call.
        os.setsid()
        # Instead of cd'ing to root, cd to the Mailman runtime directory.
        # However, before we do that, set an environment variable used by the
        # subprocesses to calculate their path to the $VAR_DIR.
        os.environ['MAILMAN_VAR_DIR'] = config.VAR_DIR
        os.chdir(config.VAR_DIR)
        # Exec the master watcher.
        execl_args = [
            sys.executable, sys.executable,
            os.path.join(config.BIN_DIR, 'master'),
            ]
        if args.force:
            execl_args.append('--force')
        # Always pass the config file path to the master projects, so there's
        # no confusion about which cfg is being used.
        execl_args.extend(['-C', config_path])
        qlog.debug('starting: %s', execl_args)
        os.execl(*execl_args)
        # We should never get here.
        raise RuntimeError('os.execl() failed')


def kill_watcher(sig):
    try:
        with open(config.PID_FILE) as fp:
            pid = int(fp.read().strip())
    except (IOError, ValueError) as error:
        # For i18n convenience
        print(_('PID unreadable in: $config.PID_FILE'), file=sys.stderr)
        print(error, file=sys.stderr)
        print(_('Is the master even running?'), file=sys.stderr)
        return
    try:
        os.kill(pid, sig)
    except OSError as error:
        if error.errno != errno.ESRCH:
            raise
        print(_('No child with pid: $pid'), file=sys.stderr)
        print(error, file=sys.stderr)
        print(_('Stale pid file removed.'), file=sys.stderr)
        os.unlink(config.PID_FILE)


@implementer(ICLISubCommand)
class SignalCommand:
    """Common base class for simple, signal sending commands."""

    name = None
    message = None
    signal = None

    def add(self, parser, command_parser):
        """See `ICLISubCommand`."""
        command_parser.add_argument(
            '-q', '--quiet',
            default=False, action='store_true',
            help=_("""\
            Don't print status messages.  Error messages are still printed to
            standard error."""))

    def process(self, args):
        """See `ICLISubCommand`."""
        if not args.quiet:
            print(_(self.message))
        kill_watcher(self.signal)


@public
class Stop(SignalCommand):
    """Stop the Mailman master and runner processes."""

    name = 'stop'
    message = _("Shutting down Mailman's master runner")
    signal = signal.SIGTERM


@public
class Reopen(SignalCommand):
    """Signal the Mailman processes to re-open their log files."""

    name = 'reopen'
    message = _('Reopening the Mailman runners')
    signal = signal.SIGHUP


@public
@implementer(ICLISubCommand)
class Restart(SignalCommand):
    """Stop and restart the Mailman runner subprocesses."""

    name = 'restart'
    message = _('Restarting the Mailman runners')
    signal = signal.SIGUSR1
