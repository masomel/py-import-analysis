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

"""SQLite database support."""

import os

from mailman.database.base import SABaseDatabase
from public import public
from urllib.parse import urlparse


@public
class SQLiteDatabase(SABaseDatabase):
    """Database class for SQLite."""

    def _prepare(self, url):
        parts = urlparse(url)
        assert parts.scheme == 'sqlite', (
            'Database url mismatch (expected sqlite prefix): {0}'.format(url))
        # Ensure that the SQLite database file has the proper permissions,
        # since SQLite doesn't play nice with umask.
        path = os.path.normpath(parts.path)
        fd = os.open(
            path,
            os.O_WRONLY | os.O_NONBLOCK | os.O_CREAT,
            0o666)
        # Ignore errors
        if fd > 0:
            os.close(fd)
