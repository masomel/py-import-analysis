# Copyright (C) 2000-2017 by the Free Software Foundation, Inc.
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

"""Archive runner."""

import copy
import logging

from datetime import datetime
from email.utils import mktime_tz, parsedate_tz
from lazr.config import as_timedelta
from mailman.config import config
from mailman.core.runner import Runner
from mailman.interfaces.archiver import ClobberDate
from mailman.interfaces.mailinglist import IListArchiverSet
from mailman.utilities.datetime import RFC822_DATE_FMT, now
from public import public


log = logging.getLogger('mailman.archiver')


def _should_clobber(msg, msgdata, archiver):
    """Should the Date header in the original message get clobbered?"""
    # Calculate the Date header of the message as a datetime.  What if there
    # are multiple Date headers, even in violation of the RFC?  For now, take
    # the first one.  If there are no Date headers, then definitely clobber.
    original_date = msg.get('date')
    if original_date is None:
        return True
    section = getattr(config.archiver, archiver, None)
    if section is None:
        log.error('No archiver config section found: {}'.format(archiver))
        return False
    try:
        clobber = ClobberDate[section.clobber_date]
    except ValueError:
        log.error('Invalid clobber_date for "{}": {}'.format(
            archiver, section.clobber_date))
        return False
    if clobber is ClobberDate.always:
        return True
    elif clobber is ClobberDate.never:
        return False
    # Maybe we'll clobber the date.  Let's see if it's farther off from now
    # than the skew period.
    skew = as_timedelta(section.clobber_skew)
    try:
        time_tuple = parsedate_tz(original_date)
    except (ValueError, OverflowError):
        # The likely cause of this is that the year in the Date: field is
        # horribly incorrect, e.g. (from SF bug # 571634):
        #
        # Date: Tue, 18 Jun 0102 05:12:09 +0500
        #
        # Obviously clobber such dates.
        return True
    if time_tuple is None:
        # There was some other bogosity in the Date header.
        return True
    claimed_date = datetime.fromtimestamp(mktime_tz(time_tuple))
    return (abs(now() - claimed_date) > skew)


@public
class ArchiveRunner(Runner):
    """The archive runner."""

    def _dispose(self, mlist, msg, msgdata):
        received_time = msgdata.get('received_time', now(strip_tzinfo=False))
        archiver_set = IListArchiverSet(mlist)
        for archiver in archiver_set.archivers:
            # The archiver is disabled if either the list-specific or
            # site-wide archiver is disabled.
            if not archiver.is_enabled:
                continue
            msg_copy = copy.deepcopy(msg)
            if _should_clobber(msg, msgdata, archiver.name):
                original_date = msg_copy['date']
                del msg_copy['date']
                del msg_copy['x-original-date']
                msg_copy['Date'] = received_time.strftime(RFC822_DATE_FMT)
                if original_date:
                    msg_copy['X-Original-Date'] = original_date
            # A problem in one archiver should not prevent other archivers
            # from running.
            try:
                archiver.system_archiver.archive_message(mlist, msg_copy)
            except Exception:
                log.exception('Exception in "{}" archiver'.format(
                    archiver.name))
