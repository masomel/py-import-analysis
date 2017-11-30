# Copyright (C) 2011-2017 by the Free Software Foundation, Inc.
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

"""Test some additional corner cases for starting/stopping."""

import os
import sys
import time
import errno
import shutil
import signal
import socket
import unittest

from contextlib import ExitStack, suppress
from datetime import datetime, timedelta
from mailman.commands.cli_control import Start, kill_watcher
from mailman.config import Configuration, config
from mailman.testing.helpers import configuration
from mailman.testing.layers import ConfigLayer
from tempfile import TemporaryDirectory


SEP = '|'


def make_config():
    # All we care about is the master process; normally it starts a bunch of
    # runners, but we don't care about any of them, so write a test
    # configuration file for the master that disables all the runners.
    new_config = 'no-runners.cfg'
    config_file = os.path.join(os.path.dirname(config.filename), new_config)
    shutil.copyfile(config.filename, config_file)
    with open(config_file, 'a') as fp:
        for runner_config in config.runner_configs:
            print('[{}]\nstart:no\n'.format(runner_config.name), file=fp)
    return config_file


def find_master():
    # See if the master process is still running.
    until = timedelta(seconds=10) + datetime.now()
    while datetime.now() < until:
        time.sleep(0.1)
        with suppress(FileNotFoundError, ValueError, ProcessLookupError):
            with open(config.PID_FILE) as fp:
                pid = int(fp.read().strip())
                os.kill(pid, 0)
                return pid
    return None


def kill_with_extreme_prejudice(pid=None):
    # 2016-12-03 barry: We have intermittent hangs during both local and CI
    # test suite runs where killing a runner or master process doesn't
    # terminate the process.  In those cases, wait()ing on the child can
    # suspend the test process indefinitely.  Locally, you have to C-c the
    # test process, but that still doesn't kill it; the process continues to
    # run in the background.  If you then search for the process's pid and
    # SIGTERM it, it will usually exit, which is why I don't understand why
    # the above SIGTERM doesn't kill it sometimes.  However, when run under
    # CI, the test suite will just hang until the CI runner times it out.  It
    # would be better to figure out the underlying cause, because we have
    # definitely seen other situations where a runner process won't exit, but
    # for testing purposes we're just trying to clean up some resources so
    # after a brief attempt at SIGTERMing it, let's SIGKILL it and warn.
    if pid is not None:
        os.kill(pid, signal.SIGTERM)
    until = timedelta(seconds=10) + datetime.now()
    while datetime.now() < until:
        try:
            if pid is None:
                os.wait3(os.WNOHANG)
            else:
                os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            # This basically means we went one too many times around the
            # loop.  The previous iteration successfully reaped the child.
            # Because the return status of wait3() and waitpid() are different
            # in those cases, it's easier just to catch the exception for
            # either call and exit.
            return
        time.sleep(0.1)
    else:
        if pid is None:
            # There's really not much more we can do because we have no pid to
            # SIGKILL.  Just report the problem and continue.
            print('WARNING: NO CHANGE IN CHILD PROCESS STATES',
                  file=sys.stderr)
            return
        print('WARNING: SIGTERM DID NOT EXIT PROCESS; SIGKILLing',
              file=sys.stderr)
        if pid is not None:
            os.kill(pid, signal.SIGKILL)
        until = timedelta(seconds=10) + datetime.now()
        while datetime.now() < until:
            status = os.waitpid(pid, os.WNOHANG)
            if status == (0, 0):
                # The child was reaped.
                return
            time.sleep(0.1)
        else:
            print('WARNING: SIGKILL DID NOT EXIT PROCESS!', file=sys.stderr)


class FakeArgs:
    force = None
    run_as_user = None
    quiet = True
    config = None


class FakeParser:
    def __init__(self):
        self.message = None

    def error(self, message):
        self.message = message
        sys.exit(1)


class TestStart(unittest.TestCase):
    """Test various starting scenarios."""

    layer = ConfigLayer

    def setUp(self):
        self.command = Start()
        self.command.parser = FakeParser()
        self.args = FakeArgs()
        self.args.config = make_config()

    def tearDown(self):
        try:
            with open(config.PID_FILE) as fp:
                master_pid = int(fp.read())
        except OSError as error:
            if error.errno != errno.ENOENT:
                raise
            # There is no master, so just ignore this.
            return
        kill_watcher(signal.SIGTERM)
        os.waitpid(master_pid, 0)

    def test_force_stale_lock(self):
        # Fake an acquisition of the master lock by another process, which
        # subsequently goes stale.  Start by finding a free process id.  Yes,
        # this could race, but given that we're starting with our own PID and
        # searching downward, it's less likely.
        fake_pid = os.getpid() - 1
        while fake_pid > 1:
            try:
                os.kill(fake_pid, 0)
            except OSError as error:
                if error.errno == errno.ESRCH:
                    break
            fake_pid -= 1
        else:
            raise RuntimeError('Cannot find free PID')
        # Lock acquisition logic taken from flufl.lock.
        claim_file = SEP.join((
            config.LOCK_FILE,
            socket.getfqdn(),
            str(fake_pid),
            '0'))
        with open(config.LOCK_FILE, 'w') as fp:
            fp.write(claim_file)
        os.link(config.LOCK_FILE, claim_file)
        expiration_date = datetime.now() - timedelta(minutes=60)
        t = time.mktime(expiration_date.timetuple())
        os.utime(claim_file, (t, t))
        # Start without --force; no master will be running.
        with suppress(SystemExit):
            self.command.process(self.args)
        self.assertIsNone(find_master())
        self.assertIn('--force', self.command.parser.message)
        # Start again, this time with --force.
        self.args.force = True
        self.command.process(self.args)
        pid = find_master()
        self.assertIsNotNone(pid)


class TestBinDir(unittest.TestCase):
    """Test issues related to bin_dir, e.g. issue #3"""

    layer = ConfigLayer

    def setUp(self):
        self.command = Start()
        self.command.parser = FakeParser()
        self.args = FakeArgs()
        self.args.config = make_config()

    def test_master_is_elsewhere(self):
        with ExitStack() as resources:
            # Patch os.fork() so that we can record the failing child process's
            # id.  We need to wait on the child exiting in either case, and
            # when it fails, no master.pid will be written.
            bin_dir = resources.enter_context(TemporaryDirectory())
            old_master = os.path.join(config.BIN_DIR, 'master')
            new_master = os.path.join(bin_dir, 'master')
            shutil.move(old_master, new_master)
            resources.callback(shutil.move, new_master, old_master)
            # Starting mailman should fail because 'master' can't be found.
            # XXX This will print Errno 2 on the console because we're not
            # silencing the child process's stderr.
            self.command.process(self.args)
            # There should be no pid file.
            args_config = Configuration()
            args_config.load(self.args.config)
            self.assertFalse(os.path.exists(args_config.PID_FILE))
            kill_with_extreme_prejudice()

    def test_master_is_elsewhere_and_findable(self):
        with ExitStack() as resources:
            bin_dir = resources.enter_context(TemporaryDirectory())
            old_master = os.path.join(config.BIN_DIR, 'master')
            new_master = os.path.join(bin_dir, 'master')
            shutil.move(old_master, new_master)
            resources.enter_context(
                configuration('paths.testing', bin_dir=bin_dir))
            resources.callback(shutil.move, new_master, old_master)
            # Starting mailman should find master in the new bin_dir.
            self.command.process(self.args)
            # There should a pid file and the process it describes should be
            # killable.  We might have to wait until the process has started.
            master_pid = find_master()
            self.assertIsNotNone(master_pid, 'master did not start')
            kill_with_extreme_prejudice(master_pid)
