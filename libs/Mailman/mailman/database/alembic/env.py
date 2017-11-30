# Copyright (C) 2014-2017 by the Free Software Foundation, Inc.
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

"""Alembic migration environment."""

from alembic import context
from contextlib import closing
from mailman.config import config
from mailman.core.initialize import initialize_1
from mailman.database.model import Model
from mailman.utilities.string import expand
from public import public
from sqlalchemy import create_engine


try:
    url = expand(config.database.url, None, config.paths)
except AttributeError:
    # Initialize config object for external alembic calls
    initialize_1()
    url = expand(config.database.url, None, config.paths)


@public
def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well.  By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script
    output.
    """
    context.configure(url=url, target_metadata=Model.metadata)
    with context.begin_transaction():
        context.run_migrations()


@public
def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    engine = create_engine(url)

    connection = engine.connect()
    with closing(connection):
        context.configure(
            connection=connection, target_metadata=Model.metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
