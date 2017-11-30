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

"""Test the archive runner."""

import os
import unittest

from email import message_from_file
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.interfaces.archiver import IArchiver
from mailman.interfaces.mailinglist import IListArchiverSet
from mailman.runners.archive import ArchiveRunner
from mailman.testing.helpers import (
    LogFileMark, configuration, get_queue_messages, make_testable_runner,
    specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import RFC822_DATE_FMT, factory, now
from zope.interface import implementer


@implementer(IArchiver)
class DummyArchiver:
    name = 'dummy'

    @staticmethod
    def list_url(mlist):
        return 'http://archive.example.com/'

    @staticmethod
    def permalink(mlist, msg):
        filename = msg['message-id-hash']
        return 'http://archive.example.com/' + filename

    @staticmethod
    def archive_message(mlist, msg):
        filename = msg['message-id-hash']
        path = os.path.join(config.MESSAGES_DIR, filename)
        with open(path, 'w') as fp:
            print(msg.as_string(), file=fp)
        # Not technically allowed by the API, but good enough for the test.
        return path


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


class TestArchiveRunner(unittest.TestCase):
    """Test the archive runner."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._now = now()
        # Enable just the dummy archiver.
        config.push('dummy', """
        [archiver.dummy]
        class: mailman.runners.tests.test_archiver.DummyArchiver
        enable: no
        [archiver.broken]
        class: mailman.runners.tests.test_archiver.BrokenArchiver
        enable: no
        [archiver.prototype]
        enable: no
        [archiver.mhonarc]
        enable: no
        [archiver.mail_archive]
        enable: no
        """)
        self.addCleanup(config.pop, 'dummy')
        self._archiveq = config.switchboards['archive']
        self._msg = mfs("""\
From: aperson@example.com
To: test@example.com
Subject: My first post
Message-ID: <first>
Message-ID-Hash: 4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB

First post!
""")
        self._runner = make_testable_runner(ArchiveRunner)
        IListArchiverSet(self._mlist).get('dummy').is_enabled = True

    @configuration('archiver.dummy', enable='yes')
    def test_archive_runner(self):
        # Ensure that the archive runner ends up archiving the message.
        self._archiveq.enqueue(
            self._msg, {},
            listid=self._mlist.list_id,
            received_time=now())
        self._runner.run()
        # There should now be a copy of the message in the file system.
        filename = os.path.join(
            config.MESSAGES_DIR, '4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB')
        with open(filename) as fp:
            archived = message_from_file(fp)
        self.assertEqual(archived['message-id'], '<first>')

    @configuration('archiver.dummy', enable='yes')
    def test_archive_runner_with_dated_message(self):
        # Date headers don't throw off the archiver runner.
        self._msg['Date'] = now(strip_tzinfo=False).strftime(RFC822_DATE_FMT)
        self._archiveq.enqueue(
            self._msg, {},
            listid=self._mlist.list_id,
            received_time=now())
        self._runner.run()
        # There should now be a copy of the message in the file system.
        filename = os.path.join(
            config.MESSAGES_DIR, '4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB')
        with open(filename) as fp:
            archived = message_from_file(fp)
        self.assertEqual(archived['message-id'], '<first>')
        self.assertEqual(archived['date'], 'Mon, 01 Aug 2005 07:49:23 +0000')

    @configuration('archiver.dummy', enable='yes', clobber_date='never')
    def test_clobber_date_never(self):
        # Even if the Date header is insanely off from the received time of
        # the message, if clobber_date is 'never', the header is not clobbered.
        self._msg['Date'] = now(strip_tzinfo=False).strftime(RFC822_DATE_FMT)
        self._archiveq.enqueue(
            self._msg, {},
            listid=self._mlist.list_id,
            received_time=now())
        self._runner.run()
        # There should now be a copy of the message in the file system.
        filename = os.path.join(
            config.MESSAGES_DIR, '4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB')
        with open(filename) as fp:
            archived = message_from_file(fp)
        self.assertEqual(archived['message-id'], '<first>')
        self.assertEqual(archived['date'], 'Mon, 01 Aug 2005 07:49:23 +0000')

    @configuration('archiver.dummy', enable='yes')
    def test_clobber_dateless(self):
        # A message with no Date header will always get clobbered.
        self.assertEqual(self._msg['date'], None)
        # Now, before enqueuing the message (well, really, calling 'now()'
        # again), fast forward a few days.
        self._archiveq.enqueue(
            self._msg, {},
            listid=self._mlist.list_id,
            received_time=now(strip_tzinfo=False))
        self._runner.run()
        # There should now be a copy of the message in the file system.
        filename = os.path.join(
            config.MESSAGES_DIR, '4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB')
        with open(filename) as fp:
            archived = message_from_file(fp)
        self.assertEqual(archived['message-id'], '<first>')
        self.assertEqual(archived['date'], 'Mon, 01 Aug 2005 07:49:23 +0000')

    @configuration('archiver.dummy', enable='yes', clobber_date='always')
    def test_clobber_date_always(self):
        # The date always gets clobbered with the current received time.
        self._msg['Date'] = now(strip_tzinfo=False).strftime(RFC822_DATE_FMT)
        # Now, before enqueuing the message (well, really, calling 'now()'
        # again as will happen in the runner), fast forward a few days.
        self._archiveq.enqueue(
            self._msg, {},
            listid=self._mlist.list_id)
        factory.fast_forward(days=4)
        self._runner.run()
        # There should now be a copy of the message in the file system.
        filename = os.path.join(
            config.MESSAGES_DIR, '4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB')
        with open(filename) as fp:
            archived = message_from_file(fp)
        self.assertEqual(archived['message-id'], '<first>')
        self.assertEqual(archived['date'], 'Fri, 05 Aug 2005 07:49:23 +0000')
        self.assertEqual(archived['x-original-date'],
                         'Mon, 01 Aug 2005 07:49:23 +0000')

    @configuration('archiver.dummy',
                   enable='yes', clobber_date='maybe', clobber_skew='1d')
    def test_clobber_date_maybe_when_insane(self):
        # The date is clobbered if it's farther off from now than its skew
        # period.
        self._msg['Date'] = now(strip_tzinfo=False).strftime(RFC822_DATE_FMT)
        # Now, before enqueuing the message (well, really, calling 'now()'
        # again as will happen in the runner), fast forward a few days.
        self._archiveq.enqueue(
            self._msg, {},
            listid=self._mlist.list_id)
        factory.fast_forward(days=4)
        self._runner.run()
        # There should now be a copy of the message in the file system.
        filename = os.path.join(
            config.MESSAGES_DIR, '4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB')
        with open(filename) as fp:
            archived = message_from_file(fp)
        self.assertEqual(archived['message-id'], '<first>')
        self.assertEqual(archived['date'], 'Fri, 05 Aug 2005 07:49:23 +0000')
        self.assertEqual(archived['x-original-date'],
                         'Mon, 01 Aug 2005 07:49:23 +0000')

    @configuration('archiver.dummy',
                   enable='yes', clobber_date='maybe', clobber_skew='10d')
    def test_clobber_date_maybe_when_sane(self):
        # The date is not clobbered if it's nearer to now than its skew
        # period.
        self._msg['Date'] = now(strip_tzinfo=False).strftime(RFC822_DATE_FMT)
        # Now, before enqueuing the message (well, really, calling 'now()'
        # again as will happen in the runner), fast forward a few days.
        self._archiveq.enqueue(
            self._msg, {},
            listid=self._mlist.list_id)
        factory.fast_forward(days=4)
        self._runner.run()
        # There should now be a copy of the message in the file system.
        filename = os.path.join(
            config.MESSAGES_DIR, '4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB')
        with open(filename) as fp:
            archived = message_from_file(fp)
        self.assertEqual(archived['message-id'], '<first>')
        self.assertEqual(archived['date'], 'Mon, 01 Aug 2005 07:49:23 +0000')
        self.assertEqual(archived['x-original-date'], None)

    @configuration('archiver.dummy', enable='yes')
    def test_disable_all_list_archivers(self):
        # Let's disable all the archivers for the mailing list, but not the
        # global archivers.  No messages will get archived.
        for archiver in IListArchiverSet(self._mlist).archivers:
            archiver.is_enabled = False
        config.db.store.commit()
        self._archiveq.enqueue(
            self._msg, {},
            listid=self._mlist.list_id)
        self._runner.run()
        self.assertEqual(os.listdir(config.MESSAGES_DIR), [])

    @configuration('archiver.broken', enable='yes')
    def test_broken_archiver(self):
        # GL issue #208 - IArchive messages raise exceptions, breaking the
        # rfc-2369 handler and shunting messages.
        mark = LogFileMark('mailman.archiver')
        self._archiveq.enqueue(
            self._msg, {},
            listid=self._mlist.list_id,
            received_time=now())
        IListArchiverSet(self._mlist).get('broken').is_enabled = True
        self._runner.run()
        # The archiver is broken, so there are no messages on the file system,
        # but there is a log message and the message was not shunted.
        log_messages = mark.read()
        self.assertIn('Exception in "broken" archiver', log_messages)
        self.assertIn('RuntimeError: Cannot archive message', log_messages)
        get_queue_messages('shunt', expected_count=0)
