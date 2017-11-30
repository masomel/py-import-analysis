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

"""Test the rfc_2369 handler."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.handlers import rfc_2369
from mailman.interfaces.archiver import ArchivePolicy, IArchiver
from mailman.testing.helpers import (
    LogFileMark, specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from urllib.parse import urljoin
from zope.interface import implementer


@implementer(IArchiver)
class DummyArchiver:
    """An example archiver which does nothing but return URLs."""
    name = 'dummy'

    def list_url(self, mlist):
        """See `IArchiver`."""
        return 'http://{}'.format(mlist.mail_host)

    def permalink(self, mlist, msg):
        """See `IArchiver`."""
        message_id_hash = msg.get('message-id-hash')
        if message_id_hash is None:
            return None
        return urljoin(self.list_url(mlist), message_id_hash)

    @staticmethod
    def archive_message(mlist, message):
        return None


@implementer(IArchiver)
class BrokenArchiver:
    """An archiver that has some broken methods."""

    name = 'broken'

    def list_url(self, mlist):
        raise RuntimeError('Cannot get list URL')

    def permalink(self, mlist, msg):
        raise RuntimeError('Cannot get permalink')

    @staticmethod
    def archive_message(mlist, message):
        raise RuntimeError('Cannot archive message')


class TestRFC2369(unittest.TestCase):
    """Test the rfc_2369 handler."""

    layer = ConfigLayer

    def setUp(self):
        config.push('no_archivers', """
        [archiver.prototype]
        enable: no
        [archiver.mail_archive]
        enable: no
        [archiver.mhonarc]
        enable: no
        [archiver.pipermail]
        enable: no
        """)
        self.addCleanup(config.pop, 'no_archivers')
        self._mlist = create_list('test@example.com')
        self._mlist.archive_policy = ArchivePolicy.public
        self._msg = mfs("""\
From: aperson@example.com
Message-ID: <first>
Message-ID-Hash: 4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB

Dummy text
""")

    def test_add_headers(self):
        # Test the addition of the Archived-At and List-Archive headers.
        config.push('archiver', """
        [archiver.dummy]
        class: {}.DummyArchiver
        enable: yes
        """.format(DummyArchiver.__module__))
        self.addCleanup(config.pop, 'archiver')
        rfc_2369.process(self._mlist, self._msg, {})
        self.assertEqual(
            self._msg.get_all('List-Archive'), ['<http://example.com>'])
        self.assertEqual(
            self._msg.get_all('Archived-At'),
            ['<http://example.com/4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB>'])

    def test_prototype_no_url(self):
        # The prototype archiver is not web-based, it must not return URLs
        config.push('archiver', """
        [archiver.prototype]
        enable: yes
        """)
        self.addCleanup(config.pop, 'archiver')
        rfc_2369.process(self._mlist, self._msg, {})
        self.assertNotIn('Archived-At', self._msg)
        self.assertNotIn('List-Archive', self._msg)

    def test_not_archived(self):
        # Messages sent to non-archived lists must not get the added headers.
        self._mlist.archive_policy = ArchivePolicy.never
        config.push('archiver', """
        [archiver.dummy]
        class: {}.DummyArchiver
        enable: yes
        """.format(DummyArchiver.__module__))
        self.addCleanup(config.pop, 'archiver')
        rfc_2369.process(self._mlist, self._msg, {})
        self.assertNotIn('List-Archive', self._msg)
        self.assertNotIn('Archived-At', self._msg)

    def test_broken_archiver(self):
        # GL issue #208 - IArchive messages raise exceptions, breaking the
        # rfc-2369 handler and shunting messages.
        config.push('archiver', """
        [archiver.broken]
        class: {}.BrokenArchiver
        enable: yes
        """.format(BrokenArchiver.__module__))
        self.addCleanup(config.pop, 'archiver')
        mark = LogFileMark('mailman.archiver')
        rfc_2369.process(self._mlist, self._msg, {})
        log_messages = mark.read()
        # Because .list_url() was broken, there will be no List-Archive header.
        self.assertIsNone(self._msg.get('list-archive'))
        self.assertIn('Exception in "broken" archiver', log_messages)
        self.assertIn('RuntimeError: Cannot get list URL', log_messages)
        # Because .permalink() was broken, there will be no Archived-At header.
        self.assertIsNone(self._msg.get('archived-at'))
        self.assertIn('Exception in "broken" archiver', log_messages)
        self.assertIn('RuntimeError: Cannot get permalink', log_messages)
