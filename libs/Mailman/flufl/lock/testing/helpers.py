"""Testing helpers."""

import os
import time
import logging
import warnings
import multiprocessing

from contextlib import ExitStack
from datetime import timedelta
from flufl.lock import Lock
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch


# For logging debugging.
log_stream = StringIO()


def make_temporary_lockfile(testobj):
    """Make a temporary lock file for the tests."""
    def lockfile_creator():
        lock_dir = testobj.resources.enter_context(TemporaryDirectory())
        return os.path.join(lock_dir, 'test.lck')
    return lockfile_creator


def child_locker(filename, lifetime, queue):
    # First, acquire the file lock.
    with Lock(filename, lifetime):
        # Now inform the parent that we've acquired the lock.
        queue.put(True)
        # Keep the file lock for a while.
        time.sleep(lifetime.seconds - 1)


def acquire(filename, lifetime=None):
    """Acquire the named lock file in a subprocess."""
    queue = multiprocessing.Queue()
    proc = multiprocessing.Process(
        target=child_locker,
        args=(filename, lifetime, queue))
    proc.start()
    while not queue.get():
        time.sleep(0.1)


def child_waitfor(filename, lifetime, queue):
    t0 = time.time()
    # Try to acquire the lock.
    with Lock(filename, lifetime):
        # Tell the parent how long it took to acquire the lock.
        queue.put(time.time() - t0)


def waitfor(filename, lifetime):
    """Fire off a child that waits for a lock."""
    queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=child_waitfor,
                                   args=(filename, lifetime, queue))
    proc.start()
    time = queue.get()
    return time


# For integration with flufl.testing.

def setup(testobj):
    testobj.resources = ExitStack()
    # Make this available to doctests.
    testobj.globs['resources'] = testobj.resources
    testobj.globs['acquire'] = acquire
    testobj.globs['waitfor'] = waitfor
    # Truncate the log.
    log_stream.truncate()
    # Note that the module has a default built-in *clock slop* of 10 seconds
    # to handle differences in machine clocks. Since this test is happening on
    # the same machine, we can bump the slop down to a more reasonable number.
    testobj.resources.enter_context(patch(
        'flufl.lock._lockfile.CLOCK_SLOP', timedelta(seconds=0)))
    testobj.globs['temporary_lockfile'] = make_temporary_lockfile(testobj)
    testobj.globs['log_stream'] = log_stream


def teardown(testobj):
    testobj.resources.close()


def start(plugin):
    if plugin.stderr:
        # Turn on lots of debugging.
        logging.getLogger('flufl.lock').setLevel(logging.DEBUG)
        warnings.filterwarnings('always', category=ResourceWarning)
    else:
        # Silence the 'lifetime has expired, breaking' message that using.rst
        # will trigger a couple of times.
        logging.getLogger('flufl.lock').setLevel(logging.CRITICAL)
