# Copyright (C) 2016-2017 by the Free Software Foundation, Inc.
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

"""Generic file cache."""

import os
import hashlib

from contextlib import ExitStack
from lazr.config import as_timedelta
from mailman.config import config
from mailman.database.model import Model
from mailman.database.transaction import dbconnection
from mailman.database.types import SAUnicode
from mailman.interfaces.cache import ICacheManager
from mailman.utilities.datetime import now
from public import public
from sqlalchemy import Boolean, Column, DateTime, Integer
from zope.interface import implementer


class CacheEntry(Model):
    __tablename__ = 'file_cache'

    id = Column(Integer, primary_key=True)
    key = Column(SAUnicode)
    file_id = Column(SAUnicode)
    is_bytes = Column(Boolean)
    created_on = Column(DateTime)
    expires_on = Column(DateTime)

    @dbconnection
    def __init__(self, store, key, file_id, is_bytes, lifetime):
        self.key = key
        self.file_id = file_id
        self.is_bytes = is_bytes
        self.created_on = now()
        self.expires_on = self.created_on + lifetime

    @dbconnection
    def update(self, store, is_bytes, lifetime):
        self.is_bytes = is_bytes
        self.created_on = now()
        self.expires_on = self.created_on + lifetime

    @property
    def is_expired(self):
        return self.expires_on <= now()


@public
@implementer(ICacheManager)
class CacheManager:
    """Manages a cache of files on the file system."""

    @staticmethod
    def _id_to_path(file_id):
        dir_1 = file_id[0:2]
        dir_2 = file_id[2:4]
        dir_path = os.path.join(config.CACHE_DIR, dir_1, dir_2)
        file_path = os.path.join(dir_path, file_id)
        return file_path, dir_path

    @staticmethod
    def _key_to_file_id(key):
        # Calculate the file-id/SHA256 hash.  The key must be a string, even
        # though the hash algorithm requires bytes.
        hashfood = key.encode('raw-unicode-escape')
        # Use the hex digest (a str) for readability.
        return hashlib.sha256(hashfood).hexdigest()

    def _write_contents(self, file_id, contents, is_bytes):
        # Calculate the file system path by taking the SHA1 hash, stripping
        # out two levels of directory (to reduce the chance of direntry
        # exhaustion on some systems).
        file_path, dir_path = self._id_to_path(file_id)
        os.makedirs(dir_path, exist_ok=True)
        # Open the file on the correct mode and write the contents.
        with ExitStack() as resources:
            if is_bytes:
                fp = resources.enter_context(open(file_path, 'wb'))
            else:
                fp = resources.enter_context(
                    open(file_path, 'w', encoding='utf-8'))
            fp.write(contents)

    @dbconnection
    def add(self, store, key, contents, lifetime=None):
        """See `ICacheManager`."""
        if lifetime is None:
            lifetime = as_timedelta(config.mailman.cache_life)
        is_bytes = isinstance(contents, bytes)
        file_id = self._key_to_file_id(key)
        # Is there already an unexpired entry under this id in the database?
        # If the entry doesn't exist, create it.  If it overwrite both the
        # contents and lifetime.
        entry = store.query(CacheEntry).filter(
            CacheEntry.key == key).one_or_none()
        if entry is None:
            entry = CacheEntry(key, file_id, is_bytes, lifetime)
            store.add(entry)
        else:
            entry.update(is_bytes, lifetime)
        self._write_contents(file_id, contents, is_bytes)
        return file_id

    @dbconnection
    def get(self, store, key, *, expunge=False):
        """See `ICacheManager`."""
        entry = store.query(CacheEntry).filter(
            CacheEntry.key == key).one_or_none()
        if entry is None:
            return None
        file_path, dir_path = self._id_to_path(entry.file_id)
        with ExitStack() as resources:
            if entry.is_bytes:
                fp = resources.enter_context(open(file_path, 'rb'))
            else:
                fp = resources.enter_context(
                    open(file_path, 'r', encoding='utf-8'))
            contents = fp.read()
        # Do we expunge the cache file?
        if expunge:
            store.delete(entry)
            os.remove(file_path)
        return contents

    @dbconnection
    def evict(self, store):
        """See `ICacheManager`."""
        # Find all the cache entries which have expired.  We can probably do
        # this more efficiently, but for now there probably aren't that many
        # cached files.
        for entry in store.query(CacheEntry):
            if entry.is_expired:
                file_path, dir_path = self._id_to_path(entry.file_id)
                os.remove(file_path)
                store.delete(entry)

    @dbconnection
    def clear(self, store):
        # Delete all the entries.  We can probably do this more efficiently,
        # but for now there probably aren't that many cached files.
        for entry in store.query(CacheEntry):
            file_path, dir_path = self._id_to_path(entry.file_id)
            os.remove(file_path)
            store.delete(entry)
