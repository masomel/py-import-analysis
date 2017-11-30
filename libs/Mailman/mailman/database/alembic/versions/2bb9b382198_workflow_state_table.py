"""Workflow state table

Revision ID: 2bb9b382198
Revises: 16c2b25c7b
Create Date: 2015-03-25 18:09:18.338790

"""

import sqlalchemy as sa

from alembic import op
from mailman.database.types import SAUnicode


# Revision identifiers, used by Alembic.
revision = '2bb9b382198'
down_revision = '16c2b25c7b'


def upgrade():
    op.create_table(
        'workflowstate',
        sa.Column('name', SAUnicode(), nullable=False),
        sa.Column('token', SAUnicode(), nullable=False),
        sa.Column('step', SAUnicode(), nullable=True),
        sa.Column('data', SAUnicode(), nullable=True),
        sa.PrimaryKeyConstraint('name', 'token')
        )


def downgrade():
    op.drop_table('workflowstate')
