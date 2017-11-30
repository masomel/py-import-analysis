"""Add member indexes

Revision ID: 33bc0099223
Revises: 42756496720
Create Date: 2015-11-19 23:04:42.449553

"""

from alembic import op
from mailman.database.helpers import is_mysql


# Revision identifiers, used by Alembic.
revision = '33bc0099223'
down_revision = '42756496720'


def upgrade():
    op.create_index(op.f('ix_address_email'),
                    'address', ['email'],
                    unique=False)
    # MySQL automatically creates the indexes for primary keys so don't need
    # to do it explicitly again.
    if not is_mysql(op.get_bind()):
        op.create_index(op.f('ix_member_address_id'),
                        'member', ['address_id'],
                        unique=False)
        op.create_index(op.f('ix_member_preferences_id'),
                        'member', ['preferences_id'],
                        unique=False)
        op.create_index(op.f('ix_member_user_id'),
                        'member', ['user_id'],
                        unique=False)


def downgrade():
    op.drop_index(op.f('ix_address_email'), table_name='address')
    # MySQL automatically creates and removes the indexes for primary keys.
    # So, you cannot drop it without removing the foreign key constraint.
    if not is_mysql(op.get_bind()):
        op.drop_index(op.f('ix_member_user_id'), table_name='member')
        op.drop_index(op.f('ix_member_preferences_id'), table_name='member')
        op.drop_index(op.f('ix_member_address_id'), table_name='member')
