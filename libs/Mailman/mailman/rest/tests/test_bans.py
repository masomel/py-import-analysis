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

"""Test address bans."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.database.transaction import transaction
from mailman.interfaces.bans import IBanManager
from mailman.testing.helpers import call_api
from mailman.testing.layers import RESTLayer
from urllib.error import HTTPError


class TestBans(unittest.TestCase):
    layer = RESTLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('ant@example.com')

    def test_get_missing_banned_address(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/ant.example.com'
                     '/bans/notbanned@example.com')
        self.assertEqual(cm.exception.code, 404)
        self.assertEqual(cm.exception.reason,
                         'Email is not banned: notbanned@example.com')

    def test_delete_missing_banned_address(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/ant.example.com'
                     '/bans/notbanned@example.com',
                     method='DELETE')
        self.assertEqual(cm.exception.code, 404)
        self.assertEqual(cm.exception.reason,
                         'Email is not banned: notbanned@example.com')

    def test_not_found_after_unbanning(self):
        manager = IBanManager(self._mlist)
        with transaction():
            manager.ban('banned@example.com')
        url = ('http://localhost:9001/3.0/lists/ant.example.com'
               '/bans/banned@example.com')
        json, response = call_api(url)
        self.assertEqual(json['email'], 'banned@example.com')
        json, response = call_api(url, method='DELETE')
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(HTTPError) as cm:
            call_api(url)
        self.assertEqual(cm.exception.code, 404)
        self.assertEqual(cm.exception.reason,
                         'Email is not banned: banned@example.com')

    def test_not_found_after_unbanning_global(self):
        manager = IBanManager(None)
        with transaction():
            manager.ban('banned@example.com')
        url = ('http://localhost:9001/3.0/bans/banned@example.com')
        json, response = call_api(url)
        self.assertEqual(json['email'], 'banned@example.com')
        json, response = call_api(url, method='DELETE')
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(HTTPError) as cm:
            call_api(url)
        self.assertEqual(cm.exception.code, 404)
        self.assertEqual(cm.exception.reason,
                         'Email is not banned: banned@example.com')

    def test_ban_missing_mailing_list(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/bee.example.com/bans')
        self.assertEqual(cm.exception.code, 404)
