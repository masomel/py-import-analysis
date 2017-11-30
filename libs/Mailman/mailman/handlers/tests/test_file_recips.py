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

"""Test file-recips handler."""

import os
import unittest

from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.testing.helpers import specialized_message_from_string as mfs
from mailman.testing.layers import ConfigLayer


class TestFileRecips(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._handler = config.handlers['file-recipients'].process
        self._msg = mfs("""\
From: aperson@example.com

A message.
""")

    def test_file_is_missing(self):
        # It is not an error for the list's the members.txt file to be
        # missing.  The missing file is just ignored.
        msgdata = {}
        self._handler(self._mlist, self._msg, msgdata)
        self.assertEqual(msgdata['recipients'], set())

    def test_file_exists(self):
        # Like above, but the file exists and contains recipients.
        path = os.path.join(self._mlist.data_path, 'members.txt')
        with open(path, 'w', encoding='utf-8') as fp:
            print('bperson@example.com', file=fp)
            print('cperson@example.com', file=fp)
            print('dperson@example.com', file=fp)
            print('eperson@example.com', file=fp)
            print('fperson@example.com', file=fp)
            print('gperson@example.com', file=fp)
        msgdata = {}
        self._handler(self._mlist, self._msg, msgdata)
        self.assertEqual(msgdata['recipients'], set((
            'bperson@example.com',
            'cperson@example.com',
            'dperson@example.com',
            'eperson@example.com',
            'fperson@example.com',
            'gperson@example.com',
            )))
