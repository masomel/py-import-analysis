# Copyright (C) 2006-2017 by the Free Software Foundation, Inc.
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

# XXX This module needs to be refactored to avoid direct access to the
# config.db global.

"""Mailman LMTP runner (server).

Most mail servers can be configured to deliver local messages via 'LMTP'[1].
This module is actually an LMTP server rather than a standard runner.

The LMTP runner opens a local TCP port and waits for the mail server to
connect to it.  The messages it receives over LMTP are very minimally parsed
for sanity and if they look okay, they are accepted and injected into
Mailman's incoming queue for normal processing.  If they don't look good, or
are destined for a bogus sub-address, they are rejected right away, hopefully
so that the peer mail server can provide better diagnostics.

[1] RFC 2033 Local Mail Transport Protocol
    http://www.faqs.org/rfcs/rfc2033.html
"""

import email
import asyncio
import logging

from aiosmtpd.controller import Controller
from aiosmtpd.lmtp import LMTP
from contextlib import suppress
from email.utils import parseaddr
from mailman.config import config
from mailman.core.runner import Runner
from mailman.database.transaction import transactional
from mailman.email.message import Message
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.runner import RunnerInterrupt
from mailman.utilities.datetime import now
from mailman.utilities.email import add_message_hash
from public import public
from zope.component import getUtility


elog = logging.getLogger('mailman.error')
qlog = logging.getLogger('mailman.runner')
slog = logging.getLogger('mailman.smtp')


# We only care about the listname and the sub-addresses as in listname@ or
# listname-request@.  This maps user visible subaddress names (which may
# include aliases) to the internal canonical subaddress name.
SUBADDRESS_NAMES = dict(
    admin='bounces',
    bounces='bounces',
    confirm='confirm',
    join='join',
    leave='leave',
    owner='owner',
    request='request',
    subscribe='join',
    unsubscribe='leave',
    )

# This maps subaddress canonical name to the destination queue that handles
# messages sent to that subaddress.
SUBADDRESS_QUEUES = dict(
    bounces='bounces',
    confirm='command',
    join='command',
    leave='command',
    owner='in',
    request='command',
    )

DASH = '-'
CRLF = '\r\n'
ERR_451 = '451 Requested action aborted: error in processing'
ERR_501 = '501 Message has defects'
ERR_502 = '502 Error: command HELO not implemented'
ERR_550 = '550 Requested action not taken: mailbox unavailable'
ERR_550_MID = '550 No Message-ID header provided'


def split_recipient(address):
    """Split an address into listname, subaddress and domain parts.

    For example:

    >>> split_recipient('mylist@example.com')
    ('mylist', None, 'example.com')

    >>> split_recipient('mylist-request@example.com')
    ('mylist', 'request', 'example.com')

    :param address: The destination address.
    :return: A 3-tuple of the form (list-shortname, subaddress, domain).
        subaddress may be None if this is the list's posting address.
    """
    localpart, domain = address.split('@', 1)
    localpart = localpart.split(config.mta.verp_delimiter, 1)[0]
    parts = localpart.split(DASH)
    if parts[-1] in SUBADDRESS_NAMES:
        listname = DASH.join(parts[:-1])
        subaddress = parts[-1]
    else:
        listname = localpart
        subaddress = None
    return listname, subaddress, domain


class LMTPHandler:
    @asyncio.coroutine
    @transactional
    def handle_DATA(self, server, session, envelope):
        try:
            # Refresh the list of list names every time we process a message
            # since the set of mailing lists could have changed.
            listnames = set(getUtility(IListManager).names)
            # Parse the message data.  If there are any defects in the
            # message, reject it right away; it's probably spam.
            msg = email.message_from_bytes(envelope.content, Message)
        except Exception:
            elog.exception('LMTP message parsing')
            config.db.abort()
            return CRLF.join(ERR_451 for to in envelope.rcpt_tos)
        # Do basic post-processing of the message, checking it for defects or
        # other missing information.
        message_id = msg.get('message-id')
        if message_id is None:
            return ERR_550_MID
        if msg.defects:
            return ERR_501
        msg.original_size = len(envelope.content)
        add_message_hash(msg)
        msg['X-MailFrom'] = envelope.mail_from
        # RFC 2033 requires us to return a status code for every recipient.
        status = []
        # Now for each address in the recipients, parse the address to first
        # see if it's destined for a valid mailing list.  If so, then queue
        # the message to the appropriate place and record a 250 status for
        # that recipient.  If not, record a failure status for that recipient.
        received_time = now()
        for to in envelope.rcpt_tos:
            try:
                to = parseaddr(to)[1].lower()
                local, subaddress, domain = split_recipient(to)
                if subaddress is not None:
                    # Check that local-subaddress is not an actual list name.
                    listname = '{}-{}@{}'.format(local, subaddress, domain)
                    if listname in listnames:
                        local = '{}-{}'.format(local, subaddress)
                        subaddress = None
                slog.debug('%s to: %s, list: %s, sub: %s, dom: %s',
                           message_id, to, local, subaddress, domain)
                listname = '{}@{}'.format(local, domain)
                if listname not in listnames:
                    status.append(ERR_550)
                    continue
                listid = '{}.{}'.format(local, domain)
                # The recipient is a valid mailing list.  Find the subaddress
                # if there is one, and set things up to enqueue to the proper
                # queue.
                queue = None
                msgdata = dict(listid=listid,
                               original_size=msg.original_size,
                               received_time=received_time)
                canonical_subaddress = SUBADDRESS_NAMES.get(subaddress)
                queue = SUBADDRESS_QUEUES.get(canonical_subaddress)
                if subaddress is None:
                    # The message is destined for the mailing list.
                    msgdata['to_list'] = True
                    queue = 'in'
                elif canonical_subaddress is None:
                    # The subaddress was bogus.
                    slog.error('%s unknown sub-address: %s',
                               message_id, subaddress)
                    status.append(ERR_550)
                    continue
                else:
                    # A valid subaddress.
                    msgdata['subaddress'] = canonical_subaddress
                    if canonical_subaddress == 'owner':
                        msgdata.update(dict(
                            to_owner=True,
                            envsender=config.mailman.site_owner,
                            ))
                        queue = 'in'
                # If we found a valid destination, enqueue the message and add
                # a success status for this recipient.
                if queue is not None:
                    config.switchboards[queue].enqueue(msg, msgdata)
                    slog.debug('%s subaddress: %s, queue: %s',
                               message_id, canonical_subaddress, queue)
                    status.append('250 Ok')
            except Exception:
                slog.exception('Queue detection: %s', msg['message-id'])
                config.db.abort()
                status.append(ERR_550)
        # All done; returning this big status string should give the expected
        # response to the LMTP client.
        return CRLF.join(status)


class LMTPController(Controller):
    def factory(self):
        server = LMTP(self.handler)
        server.__ident__ = 'GNU Mailman LMTP runner 2.0'
        return server


@public
class LMTPRunner(Runner):
    # Only __init__ is called on startup. Asyncore is responsible for later
    # connections from the MTA.  slice and numslices are ignored and are
    # necessary only to satisfy the API.

    is_queue_runner = False

    def __init__(self, name, slice=None):
        super().__init__(name, slice)
        hostname = config.mta.lmtp_host
        port = int(config.mta.lmtp_port)
        self.lmtp = LMTPController(LMTPHandler(), hostname=hostname, port=port)
        qlog.debug('LMTP server listening on %s:%s', hostname, port)

    def run(self):
        """See `IRunner`."""
        with suppress(RunnerInterrupt):
            self.lmtp.start()
            while not self._stop:
                self._snooze(0)
            self.lmtp.stop()
