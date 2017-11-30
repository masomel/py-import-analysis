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

"""Test master watcher utilities."""

import os
import tempfile
import unittest

from contextlib import suppress
from datetime import timedelta
from flufl.lock import Lock
from mailman.bin import master


class TestMasterLock(unittest.TestCase):
    def setUp(self):
        fd, self.lock_file = tempfile.mkstemp()
        os.close(fd)
        # The lock file should not exist before we try to acquire it.
        os.remove(self.lock_file)

    def tearDown(self):
        # Unlocking removes the lock file, but just to be safe (i.e. in case
        # of errors).
        with suppress(FileNotFoundError):
            os.remove(self.lock_file)

    def test_acquire_lock_1(self):
        lock = master.acquire_lock_1(False, self.lock_file)
        is_locked = lock.is_locked
        lock.unlock()
        self.assertTrue(is_locked)

    def test_master_state(self):
        my_lock = Lock(self.lock_file)
        # Mailman is not running.
        state, lock = master.master_state(self.lock_file)
        self.assertEqual(state, master.WatcherState.none)
        # Acquire the lock as if another process had already started the
        # master.  Use a timeout to avoid this test deadlocking.
        my_lock.lock(timedelta(seconds=60))
        try:
            state, lock = master.master_state(self.lock_file)
        finally:
            my_lock.unlock()
        self.assertEqual(state, master.WatcherState.conflict)
        # XXX test stale_lock and host_mismatch states.
