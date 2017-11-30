"""Add a numerical position column to sort header matches.

Revision ID: d4fbb4fd34ca
Revises: bfda02ab3a9b
Create Date: 2016-02-01 15:57:09.807678

"""

import sqlalchemy as sa

from alembic import op
from mailman.database.helpers import is_mysql


# Revision identifiers, used by Alembic.
revision = 'd4fbb4fd34ca'
down_revision = 'bfda02ab3a9b'


def upgrade():
    with op.batch_alter_table('headermatch') as batch_op:
        batch_op.add_column(
            sa.Column('position', sa.Integer(), nullable=True))
        batch_op.create_index(
            op.f('ix_headermatch_position'), ['position'], unique=False)
        if not is_mysql(op.get_bind()):
            # MySQL automatically creates indexes for primary keys.
            batch_op.create_index(
                op.f('ix_headermatch_mailing_list_id'), ['mailing_list_id'],
                unique=False)
            # MySQL doesn't allow changing columns used in a foreign key
            # constrains since MySQL version 5.6.  We need to drop the
            # constraint before changing the column.  But, since the
            # constraint name is auto-generated, we can't really hardcode the
            # name here to use batch_op.drop_constraint().  Until we have a
            # better fix for this, it should be safe to skip this.
            batch_op.alter_column(
                'mailing_list_id', existing_type=sa.INTEGER(), nullable=False)


def downgrade():
    with op.batch_alter_table('headermatch') as batch_op:
        batch_op.drop_index(op.f('ix_headermatch_position'))
        batch_op.drop_column('position')

        if not is_mysql(op.get_bind()):
            # MySQL automatically creates and removes the indexes for primary
            # keys.  So, you cannot drop it without removing the foreign key
            # constraint.
            batch_op.drop_index(op.f('ix_headermatch_mailing_list_id'))
            # MySQL doesn't allow changing columns used in foreign_key
            # constraints.
            batch_op.alter_column(
                'mailing_list_id', existing_type=sa.INTEGER(), nullable=True)
