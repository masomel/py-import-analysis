"""MailingList indexes

Revision ID: 781a38e146bf
Revises: 70af5a4e5790
Create Date: 2016-01-14 15:34:29.734429

"""

from alembic import op


# Revision identifiers, used by Alembic.
revision = '781a38e146bf'
down_revision = '70af5a4e5790'


def upgrade():
    op.create_index(
        op.f('ix_mailinglist_list_id'), 'mailinglist', ['list_id'],
        unique=True)
    op.create_index(
        op.f('ix_mailinglist_list_name'), 'mailinglist', ['list_name'],
        unique=False)
    op.create_index(
        op.f('ix_mailinglist_mail_host'), 'mailinglist', ['mail_host'],
        unique=False)


def downgrade():
    op.drop_index(op.f('ix_mailinglist_mail_host'), table_name='mailinglist')
    op.drop_index(op.f('ix_mailinglist_list_name'), table_name='mailinglist')
    op.drop_index(op.f('ix_mailinglist_list_id'), table_name='mailinglist')
