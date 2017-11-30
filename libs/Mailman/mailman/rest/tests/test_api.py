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

"""API version tests."""

import unittest

from mailman.core.system import system
from mailman.testing.helpers import call_api
from mailman.testing.layers import RESTLayer
from urllib.error import HTTPError


class TestAPIVersion(unittest.TestCase):
    layer = RESTLayer

    def test_api_31(self):
        # API version 3.1 was introduced in Mailman 3.1.
        url = 'http://localhost:9001/3.1/system'
        new = '{}/versions'.format(url)
        json, response = call_api(url)
        self.assertEqual(json['mailman_version'], system.mailman_version)
        self.assertEqual(json['python_version'], system.python_version)
        self.assertEqual(json['api_version'], '3.1')
        self.assertEqual(json['self_link'], new)

    def test_api_30(self):
        # API version 3.0 is still supported.
        url = 'http://localhost:9001/3.0/system'
        new = '{}/versions'.format(url)
        json, response = call_api(url)
        self.assertEqual(json['mailman_version'], system.mailman_version)
        self.assertEqual(json['python_version'], system.python_version)
        self.assertEqual(json['api_version'], '3.0')
        self.assertEqual(json['self_link'], new)

    def test_bad_api(self):
        # There is no API version earlier than 3.0.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/2.9/system')
        self.assertEqual(cm.exception.code, 404)
