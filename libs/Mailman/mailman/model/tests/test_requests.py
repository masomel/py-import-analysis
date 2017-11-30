# Copyright (C) 2012-2017 by the Free Software Foundation, Inc.
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

"""Test the various pending requests interfaces."""

import unittest

from contextlib import contextmanager
from itertools import count
from mailman.app.lifecycle import create_list
from mailman.app.moderator import hold_message
from mailman.config import config
from mailman.interfaces.requests import IListRequests, RequestType
from mailman.model.requests import _Request
from mailman.testing.helpers import specialized_message_from_string as mfs
from mailman.testing.layers import ConfigLayer
from sqlalchemy.event import listen, remove


@contextmanager
def before_flush(id_hacker):
    listen(config.db.store, 'before_flush', id_hacker)
    try:
        yield
    finally:
        remove(config.db.store, 'before_flush', id_hacker)


class TestRequests(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._requests_db = IListRequests(self._mlist)
        self._msg = mfs("""\
From: anne@example.com
To: ant@example.com
Subject: Something
Message-ID: <alpha>

Something else.
""")

    def test_get_request_with_type(self):
        # get_request() takes an optional request type.
        request_id = hold_message(self._mlist, self._msg)
        # Submit a request with a non-matching type.  This should return None
        # as if there were no matches.
        response = self._requests_db.get_request(
            request_id, RequestType.subscription)
        self.assertEqual(response, None)
        # Submit the same request with a matching type.
        key, data = self._requests_db.get_request(
            request_id, RequestType.held_message)
        self.assertEqual(key, '<alpha>')
        # It should also succeed with no optional request type given.
        key, data = self._requests_db.get_request(request_id)
        self.assertEqual(key, '<alpha>')

    def test_hold_with_bogus_type(self):
        # Calling hold_request() with a bogus request type is an error.
        with self.assertRaises(TypeError) as cm:
            self._requests_db.hold_request(5, 'foo')
        self.assertEqual(cm.exception.args[0], 5)

    def test_delete_missing_request(self):
        # Trying to delete a missing request is an error.
        with self.assertRaises(KeyError) as cm:
            self._requests_db.delete_request(801)
        self.assertEqual(cm.exception.args[0], 801)

    def test_only_return_this_lists_requests(self):
        # Issue #161: get_requests() returns requests that are not specific to
        # the mailing list in question.
        request_id = hold_message(self._mlist, self._msg)
        bee = create_list('bee@example.com')
        self.assertIsNone(IListRequests(bee).get_request(request_id))

    def test_request_order(self):
        # Requests must be sorted in creation order.
        #
        # This test only "works" for PostgreSQL, in the sense that if you
        # remove the fix in ../requests.py, it will still pass in SQLite.
        # Apparently SQLite auto-sorts results by ID but PostgreSQL autosorts
        # by insertion time.  It's still worth keeping the test to prevent
        # regressions.
        #
        # We modify the auto-incremented ids by listening to SQLAlchemy's
        # flush event, and hacking all the _Request object id's to the next
        # value in a descending counter.
        request_ids = []
        counter = count(200, -1)
        def id_hacker(session, flush_context, instances):         # noqa: E306
            for instance in session.new:
                if isinstance(instance, _Request):
                    instance.id = next(counter)
        with before_flush(id_hacker):
            for index in range(10):
                msg = mfs(self._msg.as_string())
                msg.replace_header('Message-ID', '<alpha{}>'.format(index))
                request_ids.append(hold_message(self._mlist, msg))
            config.db.store.flush()
        # Make sure that our ID are not already sorted.
        self.assertNotEqual(request_ids, sorted(request_ids))
        # Get requests and check their order.
        requests = self._requests_db.of_type(RequestType.held_message)
        self.assertEqual([r.id for r in requests], sorted(request_ids))
