# Copyright (C) 2012-2017 by the Free Software Foundation, Inc.
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

"""Database factory."""

import os
import types
import alembic.command

from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from flufl.lock import Lock
from mailman.config import config
from mailman.database.alembic import alembic_cfg
from mailman.database.model import Model
from mailman.interfaces.database import (
    DatabaseError, IDatabase, IDatabaseFactory)
from mailman.utilities.modules import call_name
from public import public
from sqlalchemy import MetaData
from zope.interface import implementer
from zope.interface.verify import verifyObject


LAST_STORM_SCHEMA_VERSION = '20130406000000'


@public
@implementer(IDatabaseFactory)
class DatabaseFactory:
    """Create a new database."""

    @staticmethod
    def create():
        """See `IDatabaseFactory`."""
        with Lock(os.path.join(config.LOCK_DIR, 'dbcreate.lck')):
            database_class = config.database['class']
            database = call_name(database_class)
            verifyObject(IDatabase, database)
            database.initialize()
            SchemaManager(database).setup_database()
            database.commit()
            return database


@public
class SchemaManager:
    "Manage schema migrations."""

    def __init__(self, database):
        self._database = database
        self._script = ScriptDirectory.from_config(alembic_cfg)

    def _get_storm_schema_version(self):
        metadata = MetaData()
        metadata.reflect(bind=self._database.engine)
        if 'version' not in metadata.tables:
            # There are no Storm artifacts left.
            return None
        Version = metadata.tables['version']
        last_version = self._database.store.query(Version.c.version).filter(
            Version.c.component == 'schema'
            ).order_by(Version.c.version.desc()).first()
        # Don't leave open transactions or they will block any schema change.
        self._database.commit()
        return last_version

    def setup_database(self):
        context = MigrationContext.configure(self._database.store.connection())
        current_rev = context.get_current_revision()
        head_rev = self._script.get_current_head()
        if current_rev == head_rev:
            # We're already at the latest revision so there's nothing to do.
            return head_rev
        if current_rev is None:
            # No Alembic information is available.
            storm_version = self._get_storm_schema_version()
            if storm_version is None:
                # Initial database creation.
                Model.metadata.create_all(self._database.engine)
                self._database.commit()
                alembic.command.stamp(alembic_cfg, 'head')
            else:
                # The database was previously managed by Storm.
                if storm_version.version < LAST_STORM_SCHEMA_VERSION:
                    raise DatabaseError(
                        'Upgrades skipping beta versions is not supported.')
                # Run migrations to remove the Storm-specific table and upgrade
                # to SQLAlchemy and Alembic.
                alembic.command.upgrade(alembic_cfg, 'head')
        elif current_rev != head_rev:
            alembic.command.upgrade(alembic_cfg, 'head')
        return head_rev


def _reset(self):
    """See `IDatabase`."""
    # Avoid a circular import at module level.
    from mailman.database.model import Model
    self.store.rollback()
    self._pre_reset(self.store)
    Model._reset(self)
    self._post_reset(self.store)
    self.store.commit()


@public
@implementer(IDatabaseFactory)
class DatabaseTestingFactory:
    """Create a new database for testing."""

    @staticmethod
    def create():
        """See `IDatabaseFactory`."""
        database_class = config.database['class']
        database = call_name(database_class)
        verifyObject(IDatabase, database)
        database.initialize()
        # Remove existing tables (PostgreSQL will keep them across runs)
        metadata = MetaData(bind=database.engine)
        metadata.reflect()
        metadata.drop_all()
        database.commit()
        # Now create the current model without Alembic upgrades.
        Model.metadata.create_all(database.engine)
        database.commit()
        # Make _reset() a bound method of the database instance.
        database._reset = types.MethodType(_reset, database)
        return database
