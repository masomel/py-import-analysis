# Copyright (C) 2009-2017 by the Free Software Foundation, Inc.
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

"""Fake MTA for testing purposes."""

import asyncio
import smtplib

from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message as MessageHandler
from aiosmtpd.smtp import SMTP
from mailman.interfaces.mta import IMailTransportAgentLifecycle
from public import public
from queue import Empty, Queue
from zope.interface import implementer


@public
@implementer(IMailTransportAgentLifecycle)
class FakeMTA:
    """Fake MTA for testing purposes."""

    def create(self, mlist):
        pass

    def delete(self, mlist):
        pass

    def regenerate(self, output=None):
        pass


class ConnectionCountingHandler(MessageHandler):
    def __init__(self, msg_queue):
        super().__init__()
        self._msg_queue = msg_queue
        self.connection_count = 0

    def handle_message(self, message):
        self._msg_queue.put(message)

    @asyncio.coroutine
    def handle_EHLO(self, server, session, envelope, hostname):
        session.host_name = hostname
        yield from server.push('250-AUTH PLAIN')
        return '250 HELP'

    @asyncio.coroutine
    def handle_RSET(self, server, session, envelope):
        self.connection_count = 0
        return '250 OK'


class ConnectionCountingSMTP(SMTP):
    def __init__(self, handler, oob_queue, err_queue, *args, **kws):
        super().__init__(handler, *args, **kws)
        self._auth_response = None
        self._waiting_for_auth_response = False
        self._oob_queue = oob_queue
        self._err_queue = err_queue
        self._last_error = None

    def connection_made(self, transport):
        super().connection_made(transport)
        # We can't keep the connection count on self here because the
        # controller (via the factory() method) will create a new instance of
        # this class for every connection.  The handler instance is always the
        # same though, so it's fine to stash this value away there.
        self.event_handler.connection_count += 1

    @asyncio.coroutine
    def smtp_AUTH(self, arg):
        """Record that the AUTH occurred."""
        args = arg.split()
        if args[0].lower() == 'plain':
            if len(args) == 2:
                response = args[1]
                # The second argument is the AUTH PLAIN <initial-response>
                # which must be equal to the base 64 equivalent of the
                # expected login string "testuser:testpass".
                if response == 'AHRlc3R1c2VyAHRlc3RwYXNz':
                    yield from self.push('235 Ok')
                    self._oob_queue.put(response)
                else:
                    yield from self.push('571 Bad authentication')
            else:
                assert len(args) == 1, args
                # Send a challenge and set us up to wait for the response.
                yield from self.push('334 ')
                self._waiting_for_auth_response = True
        else:
            yield from self.push('571 Bad authentication')

    @asyncio.coroutine
    def smtp_STAT(self, arg):
        """Cause the server to send statistics to its controller."""
        # Do not count the connection caused by the STAT connect.
        self.event_handler.connection_count -= 1
        self._oob_queue.put(self.event_handler.connection_count)
        yield from self.push('250 Ok')

    def _next_error(self, command):
        """Return the next error for the SMTP command, if there is one.

        :param command: The SMTP command for which an error might be
            expected.  If the next error matches the given command, the
            expected error code is returned.
        :type command: string, lower-cased
        :return: An SMTP error code
        :rtype: integer
        """
        # If the last error we pulled from the queue didn't match, then we're
        # caching it, and it might match this expected error.  If there is no
        # last error in the cache, get one from the queue now.
        if self._last_error is None:
            try:
                self._last_error = self._err_queue.get_nowait()
            except Empty:
                # No error is expected
                return None
        if self._last_error[0] == command:
            code = self._last_error[1]
            self._last_error = None
            return code
        return None

    @asyncio.coroutine
    def smtp_RCPT(self, arg):
        """For testing, sometimes cause a non-25x response."""
        code = self._next_error('rcpt')
        if code is None:
            # Everything's cool.
            yield from super().smtp_RCPT(arg)
        else:
            # The test suite wants this to fail.  The message corresponds to
            # the exception we expect smtplib.SMTP to raise.
            yield from self.push('%d Error: SMTPRecipientsRefused' % code)

    @asyncio.coroutine
    def smtp_MAIL(self, arg):
        """For testing, sometimes cause a non-25x response."""
        code = self._next_error('mail')
        if code is None:
            # Everything's cool.
            yield from super().smtp_MAIL(arg)
        else:
            # The test suite wants this to fail.  The message corresponds to
            # the exception we expect smtplib.SMTP to raise.
            yield from self.push('%d Error: SMTPResponseException' % code)


class ConnectionCountingController(Controller):
    """Count the number of SMTP connections opened."""

    def __init__(self, host, port):
        self._msg_queue = Queue()
        self._oob_queue = Queue()
        self.err_queue = Queue()
        handler = ConnectionCountingHandler(self._msg_queue)
        super().__init__(handler, hostname=host, port=port)

    def factory(self):
        return ConnectionCountingSMTP(
            self.handler, self._oob_queue, self.err_queue)

    def start(self):
        super().start()
        # Reset the connection statistics, since the base class's start()
        # method causes a connection to occur.
        self.reset()

    def _connect(self):
        client = smtplib.SMTP()
        client.connect(self.hostname, self.port)
        return client

    def get_connection_count(self):
        """Retrieve the number of connections.

        :return: The number of connections to the server that have been made.
        :rtype: integer
        """
        client = self._connect()
        client.docmd('STAT')
        # An Empty exception will occur if the data isn't available in 10
        # seconds.  Let that propagate.
        return self._oob_queue.get(block=True, timeout=10)

    def get_authentication_credentials(self):
        """Retrieve the last authentication credentials."""
        return self._oob_queue.get(block=True, timeout=10)

    def __iter__(self):
        while True:
            try:
                yield self._msg_queue.get_nowait()
            except Empty:
                raise StopIteration

    @property
    def messages(self):
        """Return all the messages received by the SMTP server."""
        yield from self

    def clear(self):
        """Clear all the messages from the queue."""
        list(self)

    def reset(self):
        client = self._connect()
        client.docmd('RSET')
