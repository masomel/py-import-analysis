"""unsubscription_workflow

Revision ID: 448a93984c35
Revises: fa0d96e28631
Create Date: 2016-06-02 14:34:24.154723
"""

import sqlalchemy as sa

from alembic import op
from mailman.database.helpers import exists_in_db
from mailman.database.types import Enum, SAUnicode
from mailman.interfaces.mailinglist import SubscriptionPolicy


# revision identifiers, used by Alembic.
revision = '448a93984c35'
down_revision = 'fa0d96e28631'


def upgrade():
    if not exists_in_db(op.get_bind(), 'mailinglist', 'unsubscription_policy'):
        # SQLite may not have removed it when downgrading.
        op.add_column('mailinglist', sa.Column(
            'unsubscription_policy', Enum(SubscriptionPolicy), nullable=True))
        # Now migrate the data.  Don't import the table definition from the
        # models, it may break this migration when the model is updated in the
        # future (see the Alembic doc).
        mlist = sa.sql.table(
            'mailinglist',
            sa.sql.column('unsubscription_policy', Enum(SubscriptionPolicy))
            )
        # There was no previous unsubscription policy.
        op.execute(mlist.update().values(
            {'unsubscription_policy':
             op.inline_literal(SubscriptionPolicy.confirm)}))
    with op.batch_alter_table('workflowstate') as batch_op:
        batch_op.drop_column('name')


def downgrade():
    with op.batch_alter_table('mailinglist') as batch_op:
        batch_op.drop_column('unsubscription_policy')
    op.add_column('workflowstate', sa.Column('name', SAUnicode))
