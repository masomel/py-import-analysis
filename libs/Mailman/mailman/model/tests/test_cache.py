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

"""Test the cache."""

import os
import unittest

from datetime import timedelta
from mailman.config import config
from mailman.interfaces.cache import ICacheManager
from mailman.testing.helpers import configuration
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import factory
from zope.component import getUtility


class TestCache(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._cachemgr = getUtility(ICacheManager)

    def test_add_str_contents(self):
        file_id = self._cachemgr.add('abc', 'xyz')
        self.assertEqual(
            file_id,
            'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        file_path = os.path.join(config.CACHE_DIR, 'ba', '78', file_id)
        self.assertTrue(os.path.exists(file_path))
        # The original content was a string.
        with open(file_path, 'r', encoding='utf-8') as fp:
            self.assertEqual(fp.read(), 'xyz')

    def test_add_bytes_contents(self):
        # No name is given so the file is cached by the hash of the contents.
        file_id = self._cachemgr.add('abc', b'xyz')
        self.assertEqual(
            file_id,
            'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
        file_path = os.path.join(config.CACHE_DIR, 'ba', '78', file_id)
        self.assertTrue(os.path.exists(file_path))
        # The original content was a string.
        with open(file_path, 'br') as fp:
            self.assertEqual(fp.read(), b'xyz')

    def test_add_overwrite(self):
        # If the file already exists and hasn't expired, a conflict exception
        # is raised the second time we try to save it.
        self._cachemgr.add('abc', 'xyz')
        self.assertEqual(self._cachemgr.get('abc'), 'xyz')
        self._cachemgr.add('abc', 'def')
        self.assertEqual(self._cachemgr.get('abc'), 'def')

    def test_get_str(self):
        # Store a str, get a str.
        self._cachemgr.add('abc', 'xyz')
        contents = self._cachemgr.get('abc')
        self.assertEqual(contents, 'xyz')

    def test_get_bytes(self):
        # Store a bytes, get a bytes.
        self._cachemgr.add('abc', b'xyz')
        contents = self._cachemgr.get('abc')
        self.assertEqual(contents, b'xyz')

    def test_get_str_expunge(self):
        # When the entry is not expunged, it can be gotten multiple times.
        # Once it's expunged, it's gone.
        self._cachemgr.add('abc', 'xyz')
        self.assertEqual(self._cachemgr.get('abc'), 'xyz')
        self.assertEqual(self._cachemgr.get('abc', expunge=True), 'xyz')
        self.assertIsNone(self._cachemgr.get('abc'))

    @configuration('mailman', cache_life='1d')
    def test_evict(self):
        # Evicting all expired cache entries makes them inaccessible.
        self._cachemgr.add('abc', 'xyz', lifetime=timedelta(hours=3))
        self._cachemgr.add('def', 'uvw', lifetime=timedelta(days=3))
        self.assertEqual(self._cachemgr.get('abc'), 'xyz')
        self.assertEqual(self._cachemgr.get('def'), 'uvw')
        factory.fast_forward(days=1)
        self._cachemgr.evict()
        self.assertIsNone(self._cachemgr.get('abc'))
        self.assertEqual(self._cachemgr.get('def'), 'uvw')

    def test_clear(self):
        # Clearing the cache gets rid of all entries, regardless of lifetime.
        self._cachemgr.add('abc', 'xyz', lifetime=timedelta(hours=3))
        self._cachemgr.add('def', 'uvw')
        self.assertEqual(self._cachemgr.get('abc'), 'xyz')
        self.assertEqual(self._cachemgr.get('def'), 'uvw')
        factory.fast_forward(days=1)
        self._cachemgr.clear()
        self.assertIsNone(self._cachemgr.get('abc'))
        self.assertIsNone(self._cachemgr.get('xyz'))
