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

"""Migration from Python 2 to Python 3.

Some columns changed from LargeBinary type to Unicode type.

Revision ID: 33e1f5f6fa8
Revises: 51b7f92bd06c
Create Date: 2015-01-20 17:32:30.144083

"""

import sqlalchemy as sa

from alembic import op
from mailman.database.helpers import is_sqlite
from mailman.database.types import SAUnicode


# Revision identifiers, used by Alembic.
revision = '33e1f5f6fa8'
down_revision = '51b7f92bd06c'


COLUMNS_TO_CHANGE = (
    ('message', 'message_id_hash'),
    ('message', 'path'),
    ('pended', 'token'),
    ('_request', 'data_hash'),
    ('user', 'password'),
    )


def upgrade():
    if is_sqlite(op.get_bind()):
        # SQLite does not support altering columns.
        return
    for table, column in COLUMNS_TO_CHANGE:
        op.alter_column(table, column, type_=SAUnicode)


def downgrade():
    if is_sqlite(op.get_bind()):
        # SQLite does not support altering columns.
        return
    for table, column in COLUMNS_TO_CHANGE:
        if op.get_bind().dialect.name == 'postgresql':
            # PostgreSQL needs the USING clause that Alembic does not support
            # yet.
            op.execute(
                ('ALTER TABLE "{table}" ALTER COLUMN "{column}" '
                 'TYPE BYTEA USING decode("{column}", \'UTF8\')').format(
                     table=table, column=column))
        else:
            op.alter_column(table, column, type_=sa.LargeBinary)
