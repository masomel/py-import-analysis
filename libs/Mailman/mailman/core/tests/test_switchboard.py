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

"""Switchboard tests."""

import os
import unittest

from mailman.config import config
from mailman.testing.helpers import (
    LogFileMark,
    specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from unittest.mock import patch


class TestSwitchboard(unittest.TestCase):
    layer = ConfigLayer

    def test_log_exception_in_finish(self):
        # If something bad happens in .finish(), the traceback should get
        # logged.  LP: #1165589.
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Message-ID: <ant>

""")
        switchboard = config.switchboards['shunt']
        # Enqueue the message.
        filebase = switchboard.enqueue(msg)
        error_log = LogFileMark('mailman.error')
        msg, data = switchboard.dequeue(filebase)
        # Now, cause .finish() to throw an exception.
        with patch('mailman.core.switchboard.os.rename',
                   side_effect=OSError('Oops!')):
            switchboard.finish(filebase, preserve=True)
        traceback = error_log.read().splitlines()
        self.assertEqual(traceback[1], 'Traceback (most recent call last):')
        self.assertEqual(traceback[-1], 'OSError: Oops!')

    def test_no_bak_but_pck(self):
        # if there is no .bak file but a .pck with the same filebase,
        # .finish() should handle the .pck.
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Message-ID: <ant>

""")
        switchboard = config.switchboards['shunt']
        # Enqueue the message.
        filebase = switchboard.enqueue(msg)
        # Now call .finish() without first dequeueing.
        switchboard.finish(filebase, preserve=True)
        # And ensure the file got preserved.
        bad_dir = config.switchboards['bad'].queue_directory
        psvfile = os.path.join(bad_dir, filebase + '.psv')
        self.assertTrue(os.path.isfile(psvfile))
