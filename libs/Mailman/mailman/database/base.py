# Copyright (C) 2006-2017 by the Free Software Foundation, Inc.
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

"""Common database support."""

import logging

from mailman.config import config
from mailman.interfaces.database import IDatabase
from mailman.utilities.string import expand
from public import public
from sqlalchemy import create_engine, event, exc, select
from sqlalchemy.orm import sessionmaker
from zope.interface import implementer


log = logging.getLogger('mailman.database')


@public
@implementer(IDatabase)
class SABaseDatabase:
    """The database base class for use with SQLAlchemy.

    Use this as a base class for your DB-Specific derived classes.
    """
    def __init__(self):
        self.url = None
        self.store = None

    def begin(self):
        """See `IDatabase`."""
        # SQLAlchemy does this for us.
        pass

    def commit(self):
        """See `IDatabase`."""
        self.store.commit()

    def abort(self):
        """See `IDatabase`."""
        self.store.rollback()

    def _pre_reset(self, store):
        """Clean up method for testing.

        This method is called during the test suite just before all the model
        tables are removed.  Override this to perform any database-specific
        pre-removal cleanup.
        """
        pass

    def _post_reset(self, store):
        """Clean up method for testing.

        This method is called during the test suite just after all the model
        tables have been removed.  Override this to perform any
        database-specific post-removal cleanup.
        """
        pass

    def _prepare(self, url):
        """Prepare the database for creation.

        Some database backends need to do so me prep work before letting Storm
        create the database.  For example, we have to touch the SQLite .db
        file first so that it has the proper file modes.
        """
        pass

    def initialize(self, debug=None):
        """See `IDatabase`."""
        # Calculate the engine url.
        url = expand(config.database.url, None, config.paths)
        self._prepare(url)
        log.debug('Database url: %s', url)
        # XXX By design of SQLite, database file creation does not honor
        # umask.  See their ticket #1193:
        # http://www.sqlite.org/cvstrac/tktview?tn=1193,31
        #
        # This sucks for us because the mailman.db file /must/ be group
        # writable, however even though we guarantee our umask is 002 here, it
        # still gets created without the necessary g+w permission, due to
        # SQLite's policy.  This should only affect SQLite engines because its
        # the only one that creates a little file on the local file system.
        # This kludges around their bug by "touch"ing the database file before
        # SQLite has any chance to create it, thus honoring the umask and
        # ensuring the right permissions.  We only try to do this for SQLite
        # engines, and yes, we could have chmod'd the file after the fact, but
        # half dozen and all...
        self.url = url
        self.engine = create_engine(url, isolation_level='READ UNCOMMITTED')
        session = sessionmaker(bind=self.engine)
        self.store = session()
        self.store.commit()
        # This is from the Dealing with Disconnects section at
        # <http://docs.sqlalchemy.org/en/latest/core/pooling.html>.  It
        # establishes connection pinging to deal with lost connections due to
        # database server restarts or other outside events.
        #
        # XXX This can all be removed once SQLAlchemy 1.2 is released, and we
        # pass `pool_pre_ping=True` to create_engine().
        @event.listens_for(self.engine, 'engine_connect')   # noqa: E306
        def ping_connection(connection, branch):            # pragma: no cover
            if branch:
                # "branch" refers to a sub-connection of a connection;
                # we don't want to bother pinging on these.
                return
            # Turn off "close with result".  This flag is only used with
            # "connectionless" execution, otherwise will be False in any case.
            old_scwr = connection.should_close_with_result
            connection.should_close_with_result = False
            try:
                # Run a SELECT 1.  Use a core select() so that the SELECT of a
                # scalar value without a table is appropriately formatted for
                # the backend.
                connection.scalar(select([1]))
            except exc.DBAPIError as error:
                # Catch SQLAlchemy's DBAPIError, which is a wrapper for the
                # DBAPI's exception.  It includes a .connection_invalidated
                # attribute which specifies if this connection is a
                # "disconnect" condition, which is based on inspection of the
                # original exception by the dialect in use.
                if error.connection_invalidated:
                    # Run the same SELECT again - the connection will
                    # re-validate itself and establish a new connection.  The
                    # disconnect detection here also causes the whole
                    # connection pool to be invalidated so that all stale
                    # connections are discarded.
                    connection.scalar(select([1]))
                else:
                    raise
            finally:
                # Restore "close with result".
                connection.should_close_with_result = old_scwr
