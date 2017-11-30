# Copyright (C) 2008-2017 by the Free Software Foundation, Inc.
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

"""Prototypical permalinking archiver."""

import os
import logging

from contextlib import suppress
from datetime import timedelta
from flufl.lock import Lock, TimeOutError
from mailbox import Maildir
from mailman.config import config
from mailman.interfaces.archiver import IArchiver
from public import public
from zope.interface import implementer


log = logging.getLogger('mailman.error')


@public
@implementer(IArchiver)
class Prototype:
    """A prototype of a third party archiver.

    Mailman proposes a draft specification for interoperability between list
    servers and archivers: <http://wiki.list.org/display/DEV/Stable+URLs>.
    """

    name = 'prototype'
    is_enabled = False

    @staticmethod
    def list_url(mlist):
        """See `IArchiver`."""
        # This archiver is not web-accessible, therefore no URL is returned.
        return None

    @staticmethod
    def permalink(mlist, msg):
        """See `IArchiver`."""
        # This archiver is not web-accessible, therefore no URL is returned.
        return None

    @staticmethod
    def archive_message(mlist, message):
        """See `IArchiver`.

        This archiver saves messages into a maildir.
        """
        archive_dir = os.path.join(config.ARCHIVE_DIR, 'prototype')
        with suppress(FileExistsError):
            os.makedirs(archive_dir, 0o775)
        # Maildir will throw an error if the directories are partially created
        # (for instance the toplevel exists but cur, new, or tmp do not)
        # therefore we don't create the toplevel as we did above.
        list_dir = os.path.join(archive_dir, mlist.fqdn_listname)
        mailbox = Maildir(list_dir, create=True, factory=None)
        lock_file = os.path.join(
            config.LOCK_DIR, '{0}-maildir.lock'.format(mlist.fqdn_listname))
        # Lock the maildir as Maildir.add() is not threadsafe.  Don't use the
        # context manager because it's not an error if we can't acquire the
        # archiver lock.  We'll just log the problem and continue.
        #
        # XXX 2012-03-14 BAW: When we extend the chain/pipeline architecture
        # to other runners, e.g. the archive runner, it would be better to let
        # any TimeOutError propagate up.  That would cause the message to be
        # re-queued and tried again later, rather than being discarded as
        # happens now below.
        lock = Lock(lock_file)
        try:
            lock.lock(timeout=timedelta(seconds=1))
            # Add the message to the maildir.  The return value could be used
            # to construct the file path if necessary.  E.g.
            #
            # os.path.join(archive_dir, mlist.fqdn_listname, 'new',
            #              message_key)
            mailbox.add(message)
        except TimeOutError:
            # Log the error and go on.
            log.error('Unable to acquire prototype archiver lock for {0}, '
                      'discarding: {1}'.format(
                          mlist.fqdn_listname,
                          message.get('message-id', 'n/a')))
        finally:
            lock.unlock(unconditionally=True)
        return None
