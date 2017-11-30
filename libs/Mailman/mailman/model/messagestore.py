# Copyright (C) 2007-2017 by the Free Software Foundation, Inc.
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

"""Model for message stores."""

import os
import errno
import pickle

from mailman.config import config
from mailman.database.transaction import dbconnection
from mailman.interfaces.messages import IMessageStore
from mailman.model.message import Message
from mailman.utilities.email import add_message_hash
from mailman.utilities.filesystem import makedirs, safe_remove
from public import public
from zope.interface import implementer


# It could be very bad if you have already stored files and you change this
# value.  We'd need a script to reshuffle and resplit.
MAX_SPLITS = 2
EMPTYSTRING = ''


@public
@implementer(IMessageStore)
class MessageStore:
    """See `IMessageStore`."""

    @dbconnection
    def add(self, store, message):
        # Ensure that the message has the requisite headers.
        message_ids = message.get_all('message-id', [])
        if len(message_ids) != 1:
            raise ValueError('Exactly one Message-ID header required')
        # Calculate and insert the Message-ID-Hash.
        message_id = message_ids[0]
        if isinstance(message_id, bytes):
            message_id = message_id.decode('ascii')
        # If the Message-ID already exists in the store, don't store it again.
        existing = store.query(Message).filter(
            Message.message_id == message_id).first()
        if existing is not None:
            return None
        hash32 = add_message_hash(message)
        # Calculate the path on disk where we're going to store this message
        # object, in pickled format.
        parts = []
        split = list(hash32)
        while split and len(parts) < MAX_SPLITS:
            parts.append(split.pop(0) + split.pop(0))
        parts.append(hash32)
        relpath = os.path.join(*parts)
        # Store the message in the database.  This relies on the database
        # providing a unique serial number, but to get this information, we
        # have to use a straight insert instead of relying on Elixir to create
        # the object.
        Message(message_id=message_id,
                message_id_hash=hash32,
                path=relpath)
        # Now calculate the full file system path.
        path = os.path.join(config.MESSAGES_DIR, relpath)
        # Write the file to the path, but catch the appropriate exception in
        # case the parent directories don't yet exist.  In that case, create
        # them and try again.
        while True:
            try:
                with open(path, 'wb') as fp:
                    # -1 says to use the highest protocol available.
                    pickle.dump(message, fp, -1)
                    break
            except IOError as error:
                if error.errno != errno.ENOENT:
                    raise
            makedirs(os.path.dirname(path))
        return hash32

    def _get_message(self, row):
        path = os.path.join(config.MESSAGES_DIR, row.path)
        with open(path, 'rb') as fp:
            return pickle.load(fp)

    @dbconnection
    def get_message_by_id(self, store, message_id):
        row = store.query(Message).filter_by(message_id=message_id).first()
        if row is None:
            return None
        return self._get_message(row)

    @dbconnection
    def get_message_by_hash(self, store, message_id_hash):
        row = store.query(Message).filter_by(
            message_id_hash=message_id_hash).first()
        if row is None:
            return None
        return self._get_message(row)

    @property
    @dbconnection
    def messages(self, store):
        for row in store.query(Message).all():
            yield self._get_message(row)

    @dbconnection
    def delete_message(self, store, message_id):
        row = store.query(Message).filter_by(message_id=message_id).first()
        if row is not None:
            path = os.path.join(config.MESSAGES_DIR, row.path)
            # It's possible that a race condition caused the file system path
            # to already be deleted.
            safe_remove(path)
            store.delete(row)
