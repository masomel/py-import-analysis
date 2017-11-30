# Copyright (C) 2006-2017 by the Free Software Foundation, Inc.
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

"""Base class for all database classes."""

from contextlib import closing
from mailman.config import config
from public import public
from sqlalchemy.ext.declarative import declarative_base


class ModelMeta:
    """The custom metaclass for all model base classes.

    This is used in the test suite to quickly reset the database after each
    test.  It works by iterating over all the tables, deleting each.  The test
    suite will then recreate the tables before each test.
    """
    @staticmethod
    def _reset(db):
        with closing(config.db.engine.connect()) as connection:
            transaction = connection.begin()
            try:
                # Delete all the tables in reverse foreign key dependency
                # order.  http://tinyurl.com/on8dy6f
                for table in reversed(Model.metadata.sorted_tables):
                    connection.execute(table.delete())
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()


Model = declarative_base(cls=ModelMeta)
public(Model=Model)
