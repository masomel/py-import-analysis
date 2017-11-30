"""Fix template password field.

Revision ID: 4bd95c99b2e7
Revises: 3002bac0c25a
Create Date: 2017-05-24 10:56:41.256602

"""

from alembic import op
from mailman.database.types import SAUnicode


# revision identifiers, used by Alembic.
revision = '4bd95c99b2e7'
down_revision = '3002bac0c25a'


def upgrade():
    with op.batch_alter_table('template') as batch_op:
        batch_op.alter_column('password', type_=SAUnicode)


def downgrade():
    # Don't go back to DateTime, it will fail if a password was set.
    pass
