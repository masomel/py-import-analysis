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

"""add_serverowner_domainowner

Revision ID: 46e92facee7
Revises: 33e1f5f6fa8
Create Date: 2015-03-20 16:01:25.007242

"""

import sqlalchemy as sa

from alembic import op
from mailman.database.helpers import exists_in_db, is_sqlite


# Revision identifiers, used by Alembic.
revision = '46e92facee7'
down_revision = '33e1f5f6fa8'


def upgrade():
    op.create_table(
        'domain_owner',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('domain_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['domain_id'], ['domain.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'domain_id')
        )
    if not exists_in_db(op.get_bind(), 'user', 'is_server_owner'):
        # SQLite may not have removed it when downgrading.
        op.add_column(
            'user',
            sa.Column('is_server_owner', sa.Boolean(), nullable=True))
    if not is_sqlite(op.get_bind()):
        op.drop_column('domain', 'contact_address')


def downgrade():
    if not is_sqlite(op.get_bind()):
        op.drop_column('user', 'is_server_owner')
    if not exists_in_db(op.get_bind(), 'domain', 'contact_address'):
        # SQLite may not have removed it.  Add a fixed length VARCHAR for
        # MySQL.
        op.add_column(
            'domain',
            sa.Column('contact_address', sa.VARCHAR(255), nullable=True))
    op.drop_table('domain_owner')
