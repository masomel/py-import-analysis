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

"""Digest functions."""

import os

from mailman.config import config
from mailman.email.message import Message
from mailman.interfaces.digests import DigestFrequency
from mailman.utilities.datetime import now as right_now
from public import public


@public
def bump_digest_number_and_volume(mlist):
    """Bump the digest number and volume."""
    now = right_now()
    if mlist.digest_last_sent_at is None:
        # There has been no previous digest.
        bump = False
    elif mlist.digest_volume_frequency == DigestFrequency.yearly:
        bump = (now.year > mlist.digest_last_sent_at.year)
    elif mlist.digest_volume_frequency == DigestFrequency.monthly:
        # Monthly.
        this_month = now.year * 100 + now.month
        digest_month = (mlist.digest_last_sent_at.year * 100 +
                        mlist.digest_last_sent_at.month)
        bump = (this_month > digest_month)
    elif mlist.digest_volume_frequency == DigestFrequency.quarterly:
        # Quarterly.
        this_quarter = now.year * 100 + (now.month - 1) // 4
        digest_quarter = (mlist.digest_last_sent_at.year * 100 +
                          (mlist.digest_last_sent_at.month - 1) // 4)
        bump = (this_quarter > digest_quarter)
    elif mlist.digest_volume_frequency == DigestFrequency.weekly:
        this_week = now.year * 100 + now.isocalendar()[1]
        digest_week = (mlist.digest_last_sent_at.year * 100 +
                       mlist.digest_last_sent_at.isocalendar()[1])
        bump = (this_week > digest_week)
    elif mlist.digest_volume_frequency == DigestFrequency.daily:
        bump = (now.toordinal() > mlist.digest_last_sent_at.toordinal())
    else:
        raise AssertionError(
            'Bad DigestFrequency: {}'.format(mlist.digest_volume_frequency))
    if bump:
        mlist.volume += 1
        mlist.next_digest_number = 1
    else:
        # Just bump the digest number.
        mlist.next_digest_number += 1
    mlist.digest_last_sent_at = now


@public
def maybe_send_digest_now(mlist, *, force=False):
    """Send this mailing list's digest now.

    If there are any messages in this mailing list's digest, the
    digest is sent immediately, regardless of whether the size
    threshold has been met.  When called through the subcommand
    `mailman send_digest` the value of .digest_send_periodic is
    consulted.

    :param mlist: The mailing list whose digest should be sent.
    :type mlist: IMailingList
    :param force: Should the digest be sent even if the size threshold hasn't
        been met?
    :type force: boolean
    """
    mailbox_path = os.path.join(mlist.data_path, 'digest.mmdf')
    # Calculate the current size of the mailbox file.  This will not tell
    # us exactly how big the resulting MIME and rfc1153 digest will
    # actually be, but it's the most easily available metric to decide
    # whether the size threshold has been reached.
    try:
        size = os.path.getsize(mailbox_path)
    except FileNotFoundError:
        size = 0
    if (size >= mlist.digest_size_threshold * 1024.0 or (force and size > 0)):
        # Send the digest.  Because we don't want to hold up this process
        # with crafting the digest, we're going to move the digest file to
        # a safe place, then craft a fake message for the DigestRunner as
        # a trigger for it to build and send the digest.
        mailbox_dest = os.path.join(
            mlist.data_path,
            'digest.{0.volume}.{0.next_digest_number}.mmdf'.format(
                mlist))
        volume = mlist.volume
        digest_number = mlist.next_digest_number
        bump_digest_number_and_volume(mlist)
        os.rename(mailbox_path, mailbox_dest)
        config.switchboards['digest'].enqueue(
            Message(),
            listid=mlist.list_id,
            digest_path=mailbox_dest,
            volume=volume,
            digest_number=digest_number)
