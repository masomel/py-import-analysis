# Copyright (C) 2016-2017 by the Free Software Foundation, Inc.
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

"""MySQL database support"""

from mailman.database.base import SABaseDatabase
from mailman.database.model import Model
from public import public


@public
class MySQLDatabase(SABaseDatabase):
    """Database class for MySQL."""

    def _post_reset(self, store):
        """Reset AUTO_INCREMENT counters for all the tables."""
        super()._post_reset(store)
        tables = reversed(Model.metadata.sorted_tables)
        for table in tables:
            store.execute('ALTER TABLE {} AUTO_INCREMENT = 1;'.format(table))
