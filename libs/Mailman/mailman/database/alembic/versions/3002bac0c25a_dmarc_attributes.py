"""dmarc_attributes

Revision ID: 3002bac0c25a
Revises: a46993b05703
Create Date: 2016-10-30 22:05:17.881880

"""

import sqlalchemy as sa

from alembic import op
from mailman.database.helpers import exists_in_db
from mailman.database.types import Enum, SAUnicodeLarge
from mailman.interfaces.mailinglist import DMARCMitigateAction


# revision identifiers, used by Alembic.
revision = '3002bac0c25a'
down_revision = 'a46993b05703'


def upgrade():
    if not exists_in_db(op.get_bind(),
                        'mailinglist',
                        'dmarc_mitigate_action'
                        ):
        # SQLite may not have removed it when downgrading.  It should be OK
        # to just test one.
        op.add_column('mailinglist', sa.Column(
            'dmarc_mitigate_action',
            Enum(DMARCMitigateAction),
            nullable=True))
        op.add_column('mailinglist', sa.Column(
            'dmarc_mitigate_unconditionally',
            sa.Boolean,
            nullable=True))
        op.add_column('mailinglist', sa.Column(
            'dmarc_moderation_notice',
            SAUnicodeLarge(),
            nullable=True))
        op.add_column('mailinglist', sa.Column(
            'dmarc_wrapped_message_text',
            SAUnicodeLarge(),
            nullable=True))
    # Now migrate the data.  Don't import the table definition from the
    # models, it may break this migration when the model is updated in the
    # future (see the Alembic doc).
    mlist = sa.sql.table(
        'mailinglist',
        sa.sql.column('dmarc_mitigate_action', Enum(DMARCMitigateAction)),
        sa.sql.column('dmarc_mitigate_unconditionally', sa.Boolean),
        sa.sql.column('dmarc_moderation_notice', SAUnicodeLarge()),
        sa.sql.column('dmarc_wrapped_message_text', SAUnicodeLarge()),
        )
    # These are all new attributes so just set defaults.
    op.execute(mlist.update().values(dict(
        dmarc_mitigate_action=op.inline_literal(
            DMARCMitigateAction.no_mitigation),
        dmarc_mitigate_unconditionally=op.inline_literal(False),
        dmarc_moderation_notice=op.inline_literal(''),
        dmarc_wrapped_message_text=op.inline_literal(''),
        )))


def downgrade():
    with op.batch_alter_table('mailinglist') as batch_op:
        batch_op.drop_column('dmarc_mitigate_action')
        batch_op.drop_column('dmarc_mitigate_unconditionally')
        batch_op.drop_column('dmarc_moderation_notice')
        batch_op.drop_column('dmarc_wrapped_message_text')
