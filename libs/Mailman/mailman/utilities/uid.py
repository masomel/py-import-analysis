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

"""Unique ID generation.

Use these functions to create unique ids rather than inlining calls to hashlib
and whatnot.  These are better instrumented for testing purposes.
"""

import os
import time
import uuid
import random
import hashlib

from contextlib import suppress
from flufl.lock import Lock
from mailman.config import config
from mailman.model.uid import UID
from mailman.testing import layers
from public import public


class _PredictableIDGenerator:
    """Base class factory.

    This factory provides a base class for unique ids that need to have
    predictable values in testing mode.
    """

    def __init__(self, context=None):
        # We can't call reset() when the factory is created below, because
        # config.VAR_DIR will not be set at that time.  So initialize it at
        # the first use.
        self._uid_file = None
        self._lock_file = None
        self._lockobj = None
        self._context = context
        layers.MockAndMonkeyLayer.register_reset(self.reset)

    @property
    def _lock(self):
        if self._lockobj is None:
            # These will get automatically cleaned up by the test
            # infrastructure.
            self._uid_file = os.path.join(config.VAR_DIR, '.uid')
            if self._context is not None:
                self._uid_file += '.' + self._context
            self._lock_file = self._uid_file + '.lock'
            self._lockobj = Lock(self._lock_file)
        return self._lockobj

    def new(self):
        """Return a new unique ID or a predictable one if in testing mode."""
        if layers.is_testing():
            # When in testing mode we want to produce predictable ids, but we
            # need to coordinate this among separate processes.  We could use
            # the database, but I don't want to add schema just to handle this
            # case, and besides transactions could get aborted, causing some
            # ids to be recycled.  So we'll use a data file with a lock.  This
            # may still not be ideal due to race conditions, but I think the
            # tests will be serialized enough (and the ids reset between
            # tests) that it will not be a problem.  Maybe.
            return self._next_predictable_id()
        return self._next_unpredictable_id()

    def _next_unpredictable_id(self):
        """Generate a unique id when Mailman is not running in testing mode.

        The type of the returned id is intended to be the type that
        makes sense for the subclass overriding this method.
        """
        raise NotImplementedError

    def _next_predictable_id(self):
        """Generate a predictable id for when Mailman being tested.

        The type of the returned id is intended to be the type that
        makes sense for the subclass overriding this method.
        """
        raise NotImplementedError

    def _next_id(self):
        with self._lock:
            try:
                with open(self._uid_file) as fp:
                    uid = int(fp.read().strip())
                    next_uid = uid + 1              # pragma: no branch
                with open(self._uid_file, 'w') as fp:
                    fp.write(str(next_uid))         # pragma: no branch
                return uid
            except FileNotFoundError:
                with open(self._uid_file, 'w') as fp:
                    fp.write('2')
                return 1

    def reset(self):
        with self._lock:
            with open(self._uid_file, 'w') as fp:
                fp.write('1')


@public
class UIDFactory(_PredictableIDGenerator):
    """A factory for unique ids."""

    def _next_unpredictable_id(self):
        """Return a new UID.

        :return: The new uid
        :rtype: uuid.UUID
        """
        while True:
            uid = uuid.uuid4()
            with suppress(ValueError):
                UID.record(uid)
                return uid

    def _next_predictable_id(self):
        uid = super()._next_id()
        return uuid.UUID(int=uid)


@public
class TokenFactory(_PredictableIDGenerator):

    def __init__(self):
        super().__init__(context='token')

    def _next_unpredictable_id(self):
        """Calculate a unique token.

        Algorithm vetted by the Timbot.  time() has high resolution on
        Linux, clock() on Windows.  random gives us about 45 bits in
        Python 2.2, 53 bits on Python 2.3.  The time and clock values
        basically help obscure the random number generator, as does the
        hash calculation.  The integral parts of the time values are
        discarded because they're the most predictable bits.
        """
        right_now = time.time()
        x = random.random() + right_now % 1.0 + time.clock() % 1.0
        # Use sha1 because it produces shorter strings.
        return hashlib.sha1(repr(x).encode('utf-8')).hexdigest()

    def _next_predictable_id(self):
        uid = super()._next_id()
        return str(uid).zfill(40)
