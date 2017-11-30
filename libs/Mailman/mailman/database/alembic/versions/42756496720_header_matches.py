"""header_matches

Revision ID: 42756496720
Revises: 2bb9b382198
Create Date: 2015-09-11 10:11:38.310315

"""

import sqlalchemy as sa

from alembic import op
from mailman.database.helpers import exists_in_db, is_sqlite
from mailman.database.types import SAUnicode

# Revision identifiers, used by Alembic.
revision = '42756496720'
down_revision = '2bb9b382198'


def upgrade():
    # Create the new table
    header_match_table = op.create_table(
        'headermatch',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mailing_list_id', sa.Integer(), nullable=True),
        sa.Column('header', SAUnicode(), nullable=False),
        sa.Column('pattern', SAUnicode(), nullable=False),
        sa.Column('chain', SAUnicode(), nullable=True),
        sa.ForeignKeyConstraint(['mailing_list_id'], ['mailinglist.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    # Now migrate the data.  It can't be offline because we need to read the
    # pickles.
    connection = op.get_bind()
    # Don't import the table definition from the models, it may break this
    # migration when the model is updated in the future (see the Alembic doc).
    mlist_table = sa.sql.table(
        'mailinglist',
        sa.sql.column('id', sa.Integer),
        sa.sql.column('header_matches', sa.PickleType)
        )
    for mlist_id, old_matches in connection.execute(mlist_table.select()):
        for old_match in old_matches:
            connection.execute(header_match_table.insert().values(
                mailing_list_id=mlist_id,
                header=old_match[0],
                pattern=old_match[1],
                chain=None
                ))
    # Now that data is migrated, drop the old column (except on SQLite which
    # does not support this)
    if not is_sqlite(connection):
        op.drop_column('mailinglist', 'header_matches')


def downgrade():
    if not exists_in_db(op.get_bind(), 'mailinglist', 'header_matches'):
        # SQLite will not have deleted the former column, since it does not
        # support column deletion.
        op.add_column(
            'mailinglist',
            sa.Column('header_matches', sa.PickleType, nullable=True))
    # Now migrate the data.  It can't be offline because we need to read the
    # pickles.
    connection = op.get_bind()
    # Don't import the table definition from the models, it may break this
    # migration when the model is updated in the future (see the Alembic doc).
    mlist_table = sa.sql.table(
        'mailinglist',
        sa.sql.column('id', sa.Integer),
        sa.sql.column('header_matches', sa.PickleType)
        )
    header_match_table = sa.sql.table(
        'headermatch',
        sa.sql.column('mailing_list_id', sa.Integer),
        sa.sql.column('header', SAUnicode),
        sa.sql.column('pattern', SAUnicode),
        )
    for mlist_id, header, pattern in connection.execute(
            header_match_table.select()).fetchall():
        mlist = connection.execute(mlist_table.select().where(
            mlist_table.c.id == mlist_id)).fetchone()
        header_matches = mlist['header_matches']
        if not header_matches:
            header_matches = []
        header_matches.append((header, pattern))
        connection.execute(mlist_table.update().where(
            mlist_table.c.id == mlist_id).values(
            header_matches=header_matches))
    op.drop_table('headermatch')
