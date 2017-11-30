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

"""PostgreSQL database support."""

from mailman.database.base import SABaseDatabase
from mailman.database.model import Model
from public import public
from sqlalchemy import Integer


@public
class PostgreSQLDatabase(SABaseDatabase):
    """Database class for PostgreSQL."""

    def _post_reset(self, store):
        """PostgreSQL-specific test suite cleanup.

        Reset the <tablename>_id_seq.last_value so that primary key ids
        restart from zero for new tests.
        """
        super()._post_reset(store)
        tables = reversed(Model.metadata.sorted_tables)
        # Recipe adapted from
        # http://stackoverflow.com/questions/544791/
        # django-postgresql-how-to-reset-primary-key
        for table in tables:
            for column in table.primary_key:
                if (column.autoincrement
                        and isinstance(column.type, Integer)      # noqa: W503
                        and not column.foreign_keys):             # noqa: W503
                    store.execute("""\
                        SELECT setval('"{0}_{1}_seq"', coalesce(max("{1}"), 1),
                                      max("{1}") IS NOT null)
                               FROM "{0}";
                        """.format(table, column.name))
