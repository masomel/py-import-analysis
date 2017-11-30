# Copyright (C) 2013-2017 by the Free Software Foundation, Inc.
#
# This file is part of GNU Mailman.
#
# GNU Mailman is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# GNU Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# GNU Mailman.  If not, see <http://www.gnu.org/licenses/>.

"""Test database schema migrations"""

import unittest
import alembic.command

from contextlib import suppress
from mailman.config import config
from mailman.database.alembic import alembic_cfg
from mailman.database.factory import LAST_STORM_SCHEMA_VERSION, SchemaManager
from mailman.database.helpers import is_mysql
from mailman.database.model import Model
from mailman.database.types import SAUnicode
from mailman.interfaces.database import DatabaseError
from mailman.testing.layers import ConfigLayer
from sqlalchemy import Column, Integer, MetaData, Table
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.schema import Index
from unittest.mock import patch


class TestSchemaManager(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        # Drop the existing model tables.
        Model.metadata.drop_all(config.db.engine)
        # Drop leftover tables (e.g. Alembic & Storm schema versions).
        md = MetaData()
        md.reflect(bind=config.db.engine)
        for table in md.sorted_tables:
            table.drop(config.db.engine)
        self.schema_mgr = SchemaManager(config.db)

    def tearDown(self):
        self._drop_storm_database()
        # Restore a virgin database.
        Model.metadata.create_all(config.db.engine)

    def _table_exists(self, tablename):
        md = MetaData()
        md.reflect(bind=config.db.engine)
        return tablename in md.tables

    def _create_storm_database(self, revision):
        version_table = Table(
            'version', Model.metadata,
            Column('id', Integer, primary_key=True),
            Column('component', SAUnicode),
            Column('version', SAUnicode),
            )
        version_table.create(config.db.engine)
        config.db.store.execute(version_table.insert().values(
            component='schema', version=revision))
        config.db.commit()
        # Other Storm specific changes, those SQL statements hopefully work on
        # all DB engines...
        config.db.engine.execute(
            'ALTER TABLE mailinglist ADD COLUMN acceptable_aliases_id INT')
        # In case of MySQL, you cannot create/drop indexes on primary keys
        # manually as it is handled automatically by MySQL.
        if not is_mysql(config.db.engine):
            Index('ix_user__user_id').drop(bind=config.db.engine)
            # Don't pollute our main metadata object, create a new one.
            md = MetaData()
            user_table = Model.metadata.tables['user'].tometadata(md)
            Index('ix_user_user_id', user_table.c._user_id).create(
                bind=config.db.engine)
        config.db.commit()

    def _drop_storm_database(self):
        """Remove the leftovers from a Storm DB.

        A drop_all() must be issued afterwards.
        """
        if 'version' in Model.metadata.tables:
            version = Model.metadata.tables['version']
            version.drop(config.db.engine, checkfirst=True)
            Model.metadata.remove(version)
        # If it's nonexistent, PostgreSQL raises a ProgrammingError while
        # SQLite raises an OperationalError. Since MySQL automatically handles
        # indexes for primary keys, don't try doing it with that backend.
        if not is_mysql(config.db.engine):
            with suppress(ProgrammingError, OperationalError):
                Index('ix_user_user_id').drop(bind=config.db.engine)
        config.db.commit()

    def test_current_database(self):
        # The database is already at the latest version.
        alembic.command.stamp(alembic_cfg, 'head')
        with patch('alembic.command') as alembic_command:
            self.schema_mgr.setup_database()
            self.assertFalse(alembic_command.stamp.called)
            self.assertFalse(alembic_command.upgrade.called)

    @patch('alembic.command.upgrade')
    def test_initial(self, alembic_command_upgrade):
        # No existing database.
        self.assertFalse(self._table_exists('mailinglist'))
        self.assertFalse(self._table_exists('alembic_version'))
        # For the initial setup of the database, the upgrade command will not
        # be called.  The tables will be created and then the schema stamped
        # at Alembic's latest revision.
        head_rev = self.schema_mgr.setup_database()
        self.assertFalse(alembic_command_upgrade.called)
        self.assertTrue(self._table_exists('mailinglist'))
        self.assertTrue(self._table_exists('alembic_version'))
        # The current Alembic revision is the same as the initial revision.
        md = MetaData()
        md.reflect(bind=config.db.engine)
        current_rev = config.db.engine.execute(
            md.tables['alembic_version'].select()).scalar()
        self.assertEqual(current_rev, head_rev)

    @patch('alembic.command')
    def test_storm(self, alembic_command):
        # Existing Storm database.
        Model.metadata.create_all(config.db.engine)
        self._create_storm_database(LAST_STORM_SCHEMA_VERSION)
        self.schema_mgr.setup_database()
        self.assertFalse(alembic_command.stamp.called)
        self.assertTrue(alembic_command.upgrade.called)

    @patch('alembic.command')
    def test_old_storm(self, alembic_command):
        # Existing Storm database in an old version.
        Model.metadata.create_all(config.db.engine)
        self._create_storm_database('001')
        self.assertRaises(DatabaseError, self.schema_mgr.setup_database)
        self.assertFalse(alembic_command.stamp.called)
        self.assertFalse(alembic_command.upgrade.called)

    def test_old_db(self):
        # The database is in an old revision, must upgrade.
        alembic.command.stamp(alembic_cfg, 'head')
        md = MetaData()
        md.reflect(bind=config.db.engine)
        config.db.store.execute(md.tables['alembic_version'].delete())
        config.db.store.execute(md.tables['alembic_version'].insert().values(
            version_num='dummyrevision'))
        config.db.commit()
        with patch('alembic.command') as alembic_command:
            self.schema_mgr.setup_database()
            self.assertFalse(alembic_command.stamp.called)
            self.assertTrue(alembic_command.upgrade.called)
