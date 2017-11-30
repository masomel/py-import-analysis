# Copyright (C) 2013-2017 by the Free Software Foundation, Inc.
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

"""Test the REST runner."""

import os
import signal
import unittest

from mailman.testing.helpers import call_api, wait_for_webservice
from mailman.testing.layers import RESTLayer


class TestRESTRunner(unittest.TestCase):
    """Test the REST runner."""

    layer = RESTLayer

    def test_sighup_restart(self):
        # The REST runner must survive a SIGHUP.
        wait_for_webservice()
        for pid in self.layer.server.runner_pids:
            os.kill(pid, signal.SIGHUP)
        wait_for_webservice()
        # This should not raise an exception.  The best way to assert this is
        # to ensure that the response is valid.
        json, response = call_api('http://localhost:9001/3.0/system/versions')
        self.assertEqual(
            json['self_link'],
            'http://localhost:9001/3.0/system/versions')
