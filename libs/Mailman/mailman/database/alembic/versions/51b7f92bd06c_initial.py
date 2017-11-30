# Copyright (C) 2014-2017 by the Free Software Foundation, Inc.
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

"""Initial migration.

This empty migration file makes sure there is always an alembic_version
in the database.  As a consequence, if the database version is reported
as None, it means the database needs to be created from scratch with
SQLAlchemy itself.

It also removes schema items left over from Storm.

Revision ID: 51b7f92bd06c
Revises: None
Create Date: 2014-10-10 09:53:35.624472
"""

import sqlalchemy as sa

from alembic import op
from mailman.database.helpers import exists_in_db, is_sqlite


# Revision identifiers, used by Alembic.
revision = '51b7f92bd06c'
down_revision = None


def upgrade():
    op.drop_table('version')
    if not is_sqlite(op.get_bind()):
        # SQLite does not support dropping columns.
        op.drop_column('mailinglist', 'acceptable_aliases_id')
    op.create_index(op.f('ix_user__user_id'), 'user',
                    ['_user_id'], unique=False)
    op.drop_index('ix_user_user_id', table_name='user')


def downgrade():
    op.create_table('version')
    op.create_index('ix_user_user_id', 'user', ['_user_id'], unique=False)
    op.drop_index(op.f('ix_user__user_id'), table_name='user')
    if not exists_in_db(op.get_bind(), 'mailinglist', 'acceptable_aliases_id'):
        op.add_column(
            'mailinglist',
            sa.Column('acceptable_aliases_id', sa.INTEGER(), nullable=True))
