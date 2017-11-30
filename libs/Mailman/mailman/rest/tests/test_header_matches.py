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

"""Test REST header matches."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.database.transaction import transaction
from mailman.interfaces.mailinglist import IHeaderMatchList
from mailman.testing.helpers import call_api
from mailman.testing.layers import RESTLayer
from urllib.error import HTTPError


class TestHeaderMatches(unittest.TestCase):
    layer = RESTLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('ant@example.com')

    def test_get_missing_header_match(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/ant.example.com'
                     '/header-matches/0')
        self.assertEqual(cm.exception.code, 404)
        self.assertEqual(cm.exception.reason,
                         'No header match at this position: 0')

    def test_delete_missing_header_match(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/ant.example.com'
                     '/header-matches/0',
                     method='DELETE')
        self.assertEqual(cm.exception.code, 404)
        self.assertEqual(cm.exception.reason,
                         'No header match at this position: 0')

    def test_add_duplicate(self):
        header_matches = IHeaderMatchList(self._mlist)
        with transaction():
            header_matches.append('header', 'pattern')
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/ant.example.com'
                     '/header-matches', {
                         'header': 'header',
                         'pattern': 'pattern',
                        })
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason,
                         'This header match already exists')

    def test_header_match_on_missing_list(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/bee.example.com'
                     '/header-matches/')
        self.assertEqual(cm.exception.code, 404)
