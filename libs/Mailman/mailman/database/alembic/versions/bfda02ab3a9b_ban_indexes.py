"""Ban indexes

Revision ID: bfda02ab3a9b
Revises: 70af5a4e5790
Create Date: 2016-01-14 16:15:44.059688

"""

from alembic import op


# Revision identifiers, used by Alembic.
revision = 'bfda02ab3a9b'
down_revision = '781a38e146bf'


def upgrade():
    op.create_index(op.f('ix_ban_email'), 'ban', ['email'], unique=False)
    op.create_index(op.f('ix_ban_list_id'), 'ban', ['list_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_ban_list_id'), table_name='ban')
    op.drop_index(op.f('ix_ban_email'), table_name='ban')
