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

"""The Mail-Archive.com archiver."""

from mailman.config import config
from mailman.config.config import external_configuration
from mailman.interfaces.archiver import ArchivePolicy, IArchiver
from public import public
from urllib.parse import quote, urljoin
from zope.interface import implementer


@public
@implementer(IArchiver)
class MailArchive:
    """Public archiver at the Mail-Archive.com.

    Messages get archived at http://go.mail-archive.com.
    """

    name = 'mail-archive'
    is_enabled = False

    def __init__(self):
        # Read our specific configuration file
        archiver_config = external_configuration(
            config.archiver.mail_archive.configuration)
        self.base_url = archiver_config.get('general', 'base_url')
        self.recipient = archiver_config.get('general', 'recipient')

    def list_url(self, mlist):
        """See `IArchiver`."""
        if mlist.archive_policy is ArchivePolicy.public:
            return urljoin(self.base_url, quote(mlist.posting_address))
        return None

    def permalink(self, mlist, msg):
        """See `IArchiver`."""
        if mlist.archive_policy is not ArchivePolicy.public:
            return None
        # It is the LMTP server's responsibility to ensure that the message has
        # a Message-ID-Hash header.  For backward compatibility, fallback to
        # searching for X-Message-ID-Hash.  If the message has neither, then
        # there's no permalink.
        message_id_hash = msg.get('message-id-hash')
        if message_id_hash is None:
            message_id_hash = msg.get('x-message-id-hash')
        if message_id_hash is None:
            return None
        if isinstance(message_id_hash, bytes):
            message_id_hash = message_id_hash.decode('ascii')
        return urljoin(self.base_url, message_id_hash)

    def archive_message(self, mlist, msg):
        """See `IArchiver`."""
        if mlist.archive_policy is ArchivePolicy.public:
            config.switchboards['out'].enqueue(
                msg,
                listid=mlist.list_id,
                recipients=[self.recipient])
        return None
