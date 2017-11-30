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

"""Test the message API."""

import unittest

from email.header import Header
from email.parser import FeedParser
from mailman.app.lifecycle import create_list
from mailman.email.message import Message, UserNotification
from mailman.testing.helpers import get_queue_messages
from mailman.testing.layers import ConfigLayer


class TestMessage(unittest.TestCase):
    """Test the message API."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._msg = UserNotification(
            'aperson@example.com',
            'test@example.com',
            'Something you need to know',
            'I needed to tell you this.')

    def test_one_precedence_header(self):
        # Ensure that when the original message already has a Precedence:
        # header, UserNotification.send(..., add_precedence=True, ...) does
        # not add a second header.
        self.assertEqual(self._msg['precedence'], None)
        self._msg['Precedence'] = 'omg wtf bbq'
        self._msg.send(self._mlist)
        items = get_queue_messages('virgin', expected_count=1)
        self.assertEqual(items[0].msg.get_all('precedence'),
                         ['omg wtf bbq'])


class TestMessageSubclass(unittest.TestCase):
    layer = ConfigLayer

    def test_i18n_filenames(self):
        parser = FeedParser(_factory=Message)
        parser.feed("""\
Message-ID: <blah@example.com>
Content-Type: multipart/mixed; boundary="------------050607040206050605060208"

This is a multi-part message in MIME format.
--------------050607040206050605060208
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: quoted-printable

Test message containing an attachment with an accented filename

--------------050607040206050605060208
Content-Disposition: attachment;
    filename*=UTF-8''d%C3%A9jeuner.txt

Test content
--------------050607040206050605060208--
""")
        msg = parser.close()
        attachment = msg.get_payload(1)
        try:
            filename = attachment.get_filename()
        except TypeError as error:
            self.fail(error)
        self.assertEqual(filename, u'd\xe9jeuner.txt')

    def test_senders_header_instances(self):
        msg = Message()
        msg['From'] = Header('test@example.com')
        # Make sure the senders property does not fail
        self.assertEqual(msg.senders, ['test@example.com'])
