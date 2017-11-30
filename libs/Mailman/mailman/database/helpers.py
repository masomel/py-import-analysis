# Copyright (C) 2015-2017 by the Free Software Foundation, Inc.
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

"""Common database helpers."""

import sqlalchemy as sa

from public import public


@public
def is_sqlite(bind):
    return bind.dialect.name == 'sqlite'


@public
def is_mysql(bind):
    return bind.dialect.name == 'mysql'


@public
def exists_in_db(bind, tablename, columnname=None):
    md = sa.MetaData()
    md.reflect(bind=bind)
    if columnname is None:
        return tablename in md.tables
    else:
        return (
            tablename in md.tables and
            columnname in [c.name for c in md.tables[tablename].columns]
            )
