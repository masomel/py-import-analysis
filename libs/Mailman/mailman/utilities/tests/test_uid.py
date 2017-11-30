# Copyright (C) 2015-2017 by the Free Software Foundation, Inc.
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

"""Test the uid module."""

import os
import uuid
import unittest

from contextlib import ExitStack
from mailman.config import config
from mailman.testing.layers import ConfigLayer
from mailman.utilities import uid
from unittest.mock import patch


class TestUID(unittest.TestCase):
    layer = ConfigLayer

    def _uid_files(self):
        return [filename
                for filename in os.listdir(os.path.join(config.VAR_DIR))
                if filename.startswith('.uid')
                ]

    def test_context(self):
        self.assertNotIn('.uid.foo', self._uid_files())
        uid.UIDFactory('foo').new()
        self.assertIn('.uid.foo', self._uid_files())

    def test_no_context(self):
        self.assertNotIn('.uid', self._uid_files())
        uid.UIDFactory().new()
        self.assertIn('.uid', self._uid_files())

    def test_unpredictable_id(self):
        with patch('mailman.utilities.uid.layers.is_testing',
                   return_value=False):
            self.assertNotEqual(uid.UIDFactory().new().int, 1)

    def test_uid_record_try_again(self):
        called = False
        def record_second(ignore):                         # noqa: E306
            nonlocal called
            if not called:
                called = True
                raise ValueError
        with ExitStack() as resources:
            resources.enter_context(
                patch('mailman.utilities.uid.layers.is_testing',
                      return_value=False))
            resources.enter_context(
                patch('mailman.utilities.uid.UID.record', record_second))
            mock = resources.enter_context(
                patch('mailman.utilities.uid.uuid.uuid4',
                      return_value=uuid.UUID(int=1)))
            uid.UIDFactory().new()
            self.assertEqual(mock.call_count, 2)

    def test_unpredictable_token_factory(self):
        with patch('mailman.utilities.uid.layers.is_testing',
                   return_value=False):
            self.assertNotEqual(uid.TokenFactory().new(),
                                '0000000000000000000000000000000000000001')
