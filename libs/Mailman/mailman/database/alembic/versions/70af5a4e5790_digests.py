"""digests

Revision ID: 70af5a4e5790
Revises: 47294d3a604
Create Date: 2015-12-19 12:05:42.202998

"""

import os
import sqlalchemy as sa

from alembic import op
from mailman.config import config


# Revision identifiers, used by Alembic.
revision = '70af5a4e5790'
down_revision = '47294d3a604'


def upgrade():
    with op.batch_alter_table('mailinglist') as batch_op:
        batch_op.alter_column('digestable',
                              new_column_name='digests_enabled',
                              existing_type=sa.Boolean)
        # All column modifications require existing types for Mysql.
        batch_op.drop_column('nondigestable')
    # Non-database migration: rename the list's data-path.
    for dirname in os.listdir(config.LIST_DATA_DIR):
        if '@' in dirname:
            old_name = os.path.join(config.LIST_DATA_DIR, dirname)
            listname, at, domain = dirname.partition('@')
            new_name = os.path.join(config.LIST_DATA_DIR,
                                    '{}.{}'.format(listname, domain))
            os.rename(old_name, new_name)


def downgrade():
    with op.batch_alter_table('mailinglist') as batch_op:
        batch_op.alter_column('digests_enabled',
                              new_column_name='digestable',
                              existing_type=sa.Boolean)
        # The data for this column is lost, it's not used anyway.
        batch_op.add_column(sa.Column('nondigestable', sa.Boolean))
    for dirname in os.listdir(config.LIST_DATA_DIR):
        if '@' not in dirname:
            old_name = os.path.join(config.LIST_DATA_DIR, dirname)
            listname, domain = dirname.split('.', 1)
            new_name = os.path.join(config.LIST_DATA_DIR,
                                    '{}@{}'.format(listname, domain))
            os.rename(old_name, new_name)
