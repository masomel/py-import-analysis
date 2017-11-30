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

"""File caches."""

from public import public
from zope.interface import Interface


@public
class ICacheManager(Interface):
    """Manager for managing cached files."""

    def add(key, contents, lifetime=None):
        """Add the contents to the cache, indexed by the key.

        If there is already some contents cached under the given key, the old
        contents are overwritten with the new contents.

        :param key: The key to use when storing the contents.
        :type name: str
        :param contents: The contents to store in the cache.  If this is a
            bytes object, it will be stored on disk in binary.  If it's a str,
            it will be stored in UTF-8.  Either way, the manager will remember
            the type and return it when you access the file.
        :type contents: bytes or str
        :param lifetime: How long should the file be cached for, before it
            expires (leading to its eventual eviction)?  If not given, the
            system default lifetime is used.
        :type lifetime: datetime.timedelta
        :return: The SHA256 hash under which the file contents are stored.
        :rtype: str
        """

    def get(key, *, expunge=False):
        """Return the contents cached under the given key.

        :param key: The key identifying the contents you want to retrieve.
        :type key: str
        :param expunge: A flag indicating whether the file contents should
            also be removed from the cache.
        :type expunge: bool
        :return: The contents of the cached file or None if the given id isn't
            in the cache (or it's already expired).
        :rtype: bytes or str, depending on the original contents.
        """

    def evict():
        """Evict all files which have expired."""

    def clear():
        """Clear the entire cache of files."""
