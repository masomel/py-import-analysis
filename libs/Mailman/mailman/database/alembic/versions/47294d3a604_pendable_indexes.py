"""Pendable indexes

Add indexes on Pendable fields that can be queried upon.


Revision ID: 47294d3a604
Revises: 33bc0099223
Create Date: 2015-12-02 11:46:47.295174

"""

import json
import sqlalchemy as sa

from alembic import op
from mailman.database.types import SAUnicode


# revision identifiers, used by Alembic.
revision = '47294d3a604'
down_revision = '3e09bb4a5dc'


TYPE_CLUES = {
    'member_id': 'probe',
    'token_owner': 'subscription',
    '_mod_message_id': 'data',
    }

pended_table = sa.sql.table(
    'pended',
    sa.sql.column('id', sa.Integer),
    )

keyvalue_table = sa.sql.table(
    'pendedkeyvalue',
    sa.sql.column('id', sa.Integer),
    sa.sql.column('key', SAUnicode),
    sa.sql.column('value', SAUnicode),
    sa.sql.column('pended_id', sa.Integer),
    )


def upgrade():
    op.create_index(
        op.f('ix_pended_expiration_date'), 'pended', ['expiration_date'],
        unique=False)
    op.create_index(op.f('ix_pended_token'), 'pended', ['token'], unique=False)
    op.create_index(
        op.f('ix_pendedkeyvalue_key'), 'pendedkeyvalue', ['key'], unique=False)
    op.create_index(
        op.f('ix_pendedkeyvalue_value'), 'pendedkeyvalue', ['value'],
        unique=False)
    # Data migration.
    connection = op.get_bind()
    for pended_result in connection.execute(pended_table.select()).fetchall():
        pended_id = pended_result['id']
        keyvalues = connection.execute(keyvalue_table.select().where(
            keyvalue_table.c.pended_id == pended_id
            )).fetchall()
        kv_type = [kv for kv in keyvalues if kv['key'] == 'type']
        if kv_type:
            # Convert existing type keys from JSON to plain text.
            # The (pended_id, key) tuple is unique.
            kv_type = kv_type[0]
            try:
                new_value = json.loads(kv_type['value'])
            except ValueError:
                # New-style entry (or already converted).
                pass
            else:
                connection.execute(keyvalue_table.update().where(
                    keyvalue_table.c.id == kv_type['id']
                    ).values(value=new_value))
        else:
            # Detect the type and add the corresponding type key.
            keys = [kv['key'] for kv in keyvalues]
            for clue_key, clue_type in TYPE_CLUES.items():
                if clue_key not in keys:
                    continue
                # We found the type, update the DB.
                connection.execute(keyvalue_table.insert().values(
                    key='type', value=clue_type, pended_id=pended_id))
                break


def downgrade():
    # Data migration.
    connection = op.get_bind()
    # Remove the introduced type keys.
    connection.execute(keyvalue_table.delete().where(sa.and_(
        keyvalue_table.c.key == 'type',
        keyvalue_table.c.value.in_(TYPE_CLUES.values())
        )))
    # Convert the other type keys to JSON.
    keyvalues = connection.execute(keyvalue_table.select().where(
        keyvalue_table.c.key == 'type')).fetchall()
    for keyvalue in keyvalues:
        connection.execute(keyvalue_table.update().where(
            keyvalue_table.c.id == keyvalue['id']
            ).values(value=json.dumps(keyvalue['value'])))
    # Remove indexes.
    op.drop_index(op.f('ix_pendedkeyvalue_value'), table_name='pendedkeyvalue')
    op.drop_index(op.f('ix_pendedkeyvalue_key'), table_name='pendedkeyvalue')
    op.drop_index(op.f('ix_pended_token'), table_name='pended')
    op.drop_index(op.f('ix_pended_expiration_date'), table_name='pended')
