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

"""Additional tests for the top-level owners resource."""

import unittest

from mailman.testing.helpers import call_api
from mailman.testing.layers import RESTLayer
from urllib.error import HTTPError


class TestOwners(unittest.TestCase):
    layer = RESTLayer

    def test_bogus_trailing_path(self):
        # Nothing is allowed after the top-level /owners resource.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/owners/anne')
        self.assertEqual(cm.exception.code, 400)
