"""Add indexes on the Member table.

Revision ID: 3e09bb4a5dc
Revises: 33bc0099223
Create Date: 2015-12-11 19:16:57.030395

"""

from alembic import op


# Revision identifiers, used by Alembic.
revision = '3e09bb4a5dc'
down_revision = '33bc0099223'


def upgrade():
    op.create_index(
        op.f('ix_member_list_id'), 'member', ['list_id'], unique=False)
    op.create_index(
        op.f('ix_member_role'), 'member', ['role'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_member_role'), table_name='member')
    op.drop_index(op.f('ix_member_list_id'), table_name='member')
