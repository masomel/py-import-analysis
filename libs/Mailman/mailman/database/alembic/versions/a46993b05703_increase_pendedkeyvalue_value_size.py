"""increase pendedkeyvalue value size

Revision ID: a46993b05703
Revises: 448a93984c35
Create Date: 2016-12-15 20:43:48.520837

"""

from alembic import op
from mailman.database.types import SAUnicode, SAUnicodeLarge


# revision identifiers, used by Alembic.
revision = 'a46993b05703'
down_revision = '448a93984c35'


def upgrade():
    # Adding another rule can make the rule Hits/Misses too long for MySQL
    # SaUnicode.
    with op.batch_alter_table('pendedkeyvalue') as batch_op:
        batch_op.alter_column('value', type_=SAUnicodeLarge)


def downgrade():
    with op.batch_alter_table('pendedkeyvalue') as batch_op:
        batch_op.alter_column('value', type_=SAUnicode)
