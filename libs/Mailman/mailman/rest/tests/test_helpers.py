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

"""Additional tests for helpers."""

import json
import unittest

from datetime import timedelta
from email.header import Header
from email.message import Message
from mailman.rest import helpers
from mailman.testing.layers import ConfigLayer, RESTLayer


class FakeResponse:
    def __init__(self):
        self.body = 'not set'


class Unserializable:
    pass


class TestHelpers(unittest.TestCase):
    layer = ConfigLayer

    def test_not_found_body_is_none(self):
        response = FakeResponse()
        helpers.not_found(response, body=None)
        self.assertEqual(response.body, 'not set')

    def test_accepted_body_is_not_none(self):
        response = FakeResponse()
        helpers.accepted(response, body='set')
        self.assertEqual(response.body, 'set')

    def test_bad_request_body_is_none(self):
        response = FakeResponse()
        helpers.bad_request(response, body=None)
        self.assertEqual(response.body, 'not set')

    def test_conflict_body_is_none(self):
        response = FakeResponse()
        helpers.conflict(response, body=None)
        self.assertEqual(response.body, 'not set')

    def test_forbidden_body_is_none(self):
        response = FakeResponse()
        helpers.forbidden(response, body=None)
        self.assertEqual(response.body, 'not set')

    def test_json_encoding_datetime_seconds(self):
        resource = dict(interval=timedelta(seconds=2))
        unjson = eval(helpers.etag(resource))
        self.assertEqual(unjson['interval'], '0d2.0s')

    def test_json_encoding_datetime_microseconds(self):
        resource = dict(interval=timedelta(microseconds=2))
        unjson = eval(helpers.etag(resource))
        self.assertEqual(unjson['interval'], '0d2e-06s')

    def test_json_encoding_default(self):
        resource = dict(interval=Unserializable())
        self.assertRaises(TypeError, helpers.etag, resource)


class TestJSONEncoder(unittest.TestCase):
    """Test the JSON ExtendedEncoder."""
    layer = RESTLayer

    def test_encode_message(self):
        msg = Message()
        msg['From'] = 'test@example.com'
        msg.set_payload('Test content.')
        result = json.dumps(msg, cls=helpers.ExtendedEncoder)
        self.assertEqual(
            result, json.dumps('From: test@example.com\n\nTest content.'))

    def test_encode_header(self):
        value = 'Contains non-ascii \u00e9 \u00e7 \u00e0'
        result = json.dumps(
            Header(value, charset='utf-8'),
            cls=helpers.ExtendedEncoder)
        self.assertEqual(result, json.dumps(value))
