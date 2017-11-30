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

"""Digest helper tests."""

import os
import unittest

from datetime import timedelta
from mailman.app.digests import (
    bump_digest_number_and_volume, maybe_send_digest_now)
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.interfaces.digests import DigestFrequency
from mailman.interfaces.member import DeliveryMode
from mailman.runners.digest import DigestRunner
from mailman.testing.helpers import (
    get_queue_messages, make_testable_runner,
    specialized_message_from_string as mfs, subscribe)
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import factory, now as right_now


class TestBumpDigest(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._mlist.volume = 7
        self._mlist.next_digest_number = 4
        self.right_now = right_now()

    def test_bump_no_previous_digest(self):
        self._mlist.digest_last_sent_at = None
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 7)
        self.assertEqual(self._mlist.next_digest_number, 5)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_yearly(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            days=-370)
        self._mlist.digest_volume_frequency = DigestFrequency.yearly
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 8)
        self.assertEqual(self._mlist.next_digest_number, 1)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_yearly_not_yet(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            days=-200)
        self._mlist.digest_volume_frequency = DigestFrequency.yearly
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 7)
        self.assertEqual(self._mlist.next_digest_number, 5)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_monthly(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            days=-32)
        self._mlist.digest_volume_frequency = DigestFrequency.monthly
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 8)
        self.assertEqual(self._mlist.next_digest_number, 1)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_monthly_not_yet(self):
        # The normal test date starts on the first day of the month, so let's
        # fast forward it a few days so we can set the digest last sent time
        # to earlier in the same month.
        self._mlist.digest_last_sent_at = self.right_now
        factory.fast_forward(days=26)
        self._mlist.digest_volume_frequency = DigestFrequency.monthly
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 7)
        self.assertEqual(self._mlist.next_digest_number, 5)
        self.assertEqual(self._mlist.digest_last_sent_at, right_now())

    def test_bump_quarterly(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            days=-93)
        self._mlist.digest_volume_frequency = DigestFrequency.quarterly
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 8)
        self.assertEqual(self._mlist.next_digest_number, 1)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_quarterly_not_yet(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            days=-88)
        self._mlist.digest_volume_frequency = DigestFrequency.quarterly
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 7)
        self.assertEqual(self._mlist.next_digest_number, 5)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_weekly(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            days=-8)
        self._mlist.digest_volume_frequency = DigestFrequency.weekly
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 8)
        self.assertEqual(self._mlist.next_digest_number, 1)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_weekly_not_yet(self):
        # The normal test date starts on the first day of the week, so let's
        # fast forward it a few days so we can set the digest last sent time
        # to earlier in the same week.
        self._mlist.digest_last_sent_at = self.right_now
        factory.fast_forward(days=3)
        self._mlist.digest_volume_frequency = DigestFrequency.weekly
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 7)
        self.assertEqual(self._mlist.next_digest_number, 5)
        self.assertEqual(self._mlist.digest_last_sent_at, right_now())

    def test_bump_daily(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            hours=-27)
        self._mlist.digest_volume_frequency = DigestFrequency.daily
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 8)
        self.assertEqual(self._mlist.next_digest_number, 1)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_daily_not_yet(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            hours=-5)
        self._mlist.digest_volume_frequency = DigestFrequency.daily
        bump_digest_number_and_volume(self._mlist)
        self.assertEqual(self._mlist.volume, 7)
        self.assertEqual(self._mlist.next_digest_number, 5)
        self.assertEqual(self._mlist.digest_last_sent_at, self.right_now)

    def test_bump_bad_frequency(self):
        self._mlist.digest_last_sent_at = self.right_now + timedelta(
            hours=-22)
        self._mlist.digest_volume_frequency = -10
        self.assertRaises(AssertionError,
                          bump_digest_number_and_volume, self._mlist)


class TestMaybeSendDigest(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._mlist.send_welcome_message = False
        self._mailbox_path = os.path.join(self._mlist.data_path, 'digest.mmdf')
        # The mailing list needs at least one digest recipient.
        member = subscribe(self._mlist, 'Anne')
        member.preferences.delivery_mode = DeliveryMode.plaintext_digests
        self._subject_number = 1
        self._runner = make_testable_runner(DigestRunner, 'digest')

    def _to_digest(self, count=1):
        for i in range(count):
            msg = mfs("""\
To: ant@example.com
From: anne@example.com
Subject: message {}

""".format(self._subject_number))
            self._subject_number += 1
            config.handlers['to-digest'].process(self._mlist, msg, {})

    def test_send_digest_over_threshold(self):
        # Put a few messages in the digest.
        self._to_digest(3)
        # Set the size threshold low enough to trigger a send.
        self._mlist.digest_size_threshold = 0.1
        maybe_send_digest_now(self._mlist)
        self._runner.run()
        # There are no digests in flight now, and a single digest message has
        # been sent.
        get_queue_messages('digest', expected_count=0)
        self.assertFalse(os.path.exists(self._mailbox_path))
        items = get_queue_messages('virgin', expected_count=1)
        digest_contents = str(items[0].msg)
        self.assertIn('Subject: message 1', digest_contents)
        self.assertIn('Subject: message 2', digest_contents)

    def test_dont_send_digest_under_threshold(self):
        # Put a few messages in the digest.
        self._to_digest(3)
        # Set the size threshold high enough to not trigger a send.
        self._mlist.digest_size_threshold = 100
        maybe_send_digest_now(self._mlist)
        self._runner.run()
        # A digest is still being collected, but none have been sent.
        get_queue_messages('digest', expected_count=0)
        self.assertGreater(os.path.getsize(self._mailbox_path), 0)
        self.assertLess(os.path.getsize(self._mailbox_path), 100 * 1024.0)
        get_queue_messages('virgin', expected_count=0)

    def test_force_send_digest_under_threshold(self):
        # Put a few messages in the digest.
        self._to_digest(3)
        # Set the size threshold high enough to not trigger a send.
        self._mlist.digest_size_threshold = 100
        # Force sending a digest anyway.
        maybe_send_digest_now(self._mlist, force=True)
        self._runner.run()
        # There are no digests in flight now, and a single digest message has
        # been sent.
        get_queue_messages('digest', expected_count=0)
        self.assertFalse(os.path.exists(self._mailbox_path))
        items = get_queue_messages('virgin', expected_count=1)
        digest_contents = str(items[0].msg)
        self.assertIn('Subject: message 1', digest_contents)
        self.assertIn('Subject: message 2', digest_contents)
