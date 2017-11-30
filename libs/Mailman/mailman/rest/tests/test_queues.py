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

"""Test the `queues` resource."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.database.transaction import transaction
from mailman.testing.helpers import call_api, get_queue_messages
from mailman.testing.layers import RESTLayer
from urllib.error import HTTPError


TEXT = """\
From: anne@example.com
To: test@example.com
Subject: A test
Message-ID: <ant>

"""


class TestQueues(unittest.TestCase):
    layer = RESTLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('test@example.com')

    def test_missing_queue(self):
        # Trying to print a missing queue gives a 404.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/queues/notaq')
        self.assertEqual(cm.exception.code, 404)

    def test_no_such_list(self):
        # POSTing to a queue with a bad list-id gives a 400.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/queues/bad', {
                'list_id': 'nosuchlist.example.com',
                'text': TEXT,
                })
        self.assertEqual(cm.exception.code, 400)

    def test_inject(self):
        # Injecting a message leaves the message in the queue.
        starting_messages = get_queue_messages('bad')
        self.assertEqual(len(starting_messages), 0)
        content, response = call_api('http://localhost:9001/3.0/queues/bad', {
            'list_id': 'test.example.com',
            'text': TEXT})
        self.assertEqual(response.status_code, 201)
        location = response.headers['location']
        filebase = location.split('/')[-1]
        # The message is in the 'bad' queue.
        content, response = call_api('http://localhost:9001/3.0/queues/bad')
        files = content['files']
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], filebase)
        # Verify the files directly.
        files = list(config.switchboards['bad'].files)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], filebase)
        # Verify the content.
        items = get_queue_messages('bad')
        self.assertEqual(len(items), 1)
        msg = items[0].msg
        # Remove some headers that get added by Mailman.
        del msg['date']
        self.assertEqual(msg['message-id-hash'],
                         'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')
        del msg['message-id-hash']
        del msg['x-message-id-hash']
        self.assertMultiLineEqual(msg.as_string(), TEXT)

    def test_delete_file(self):
        # Inject a file, then delete it.
        content, response = call_api('http://localhost:9001/3.0/queues/bad', {
            'list_id': 'test.example.com',
            'text': TEXT})
        location = response.headers['location']
        self.assertEqual(len(config.switchboards['bad'].files), 1)
        # Delete the file through REST.
        content, response = call_api(location, method='DELETE')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(config.switchboards['bad'].files), 0)
