# Copyright (C) 2011-2017 by the Free Software Foundation, Inc.
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

"""Additional tests for the hold chain."""

import unittest

from email import message_from_bytes as mfb
from mailman.app.lifecycle import create_list
from mailman.chains.hold import autorespond_to_sender
from mailman.core.chains import process as process_chain
from mailman.interfaces.autorespond import IAutoResponseSet, Response
from mailman.interfaces.member import MemberRole
from mailman.interfaces.messages import IMessageStore
from mailman.interfaces.requests import IListRequests, RequestType
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import (
    LogFileMark, configuration, get_queue_messages, set_preferred,
    specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from pkg_resources import resource_filename
from zope.component import getUtility


class TestAutorespond(unittest.TestCase):
    """Test autorespond_to_sender()"""

    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        self._mlist = create_list('test@example.com')

    @configuration('mta', max_autoresponses_per_day=1)
    def test_max_autoresponses_per_day(self):
        # The last one we sent was the last one we should send today.  Instead
        # of sending an automatic response, send them the "no more today"
        # message.  Start by simulating a response having been sent to an
        # address already.
        anne = getUtility(IUserManager).create_address('anne@example.com')
        response_set = IAutoResponseSet(self._mlist)
        response_set.response_sent(anne, Response.hold)
        # Trigger the sending of a "last response for today" using the default
        # language (i.e. the mailing list's preferred language).
        autorespond_to_sender(self._mlist, 'anne@example.com')
        # So first, there should be one more hold response sent to the user.
        self.assertEqual(response_set.todays_count(anne, Response.hold), 2)
        # And the virgin queue should have the message in it.
        messages = get_queue_messages('virgin')
        self.assertEqual(len(messages), 1)
        # Remove the variable headers.
        message = messages[0].msg
        self.assertIn('message-id', message)
        del message['message-id']
        self.assertIn('date', message)
        del message['date']
        self.assertMultiLineEqual(messages[0].msg.as_string(), """\
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Subject: Last autoresponse notification for today
From: test-owner@example.com
To: anne@example.com
Precedence: bulk

We have received a message from your address <anne@example.com>
requesting an automated response from the test@example.com mailing
list.

The number we have seen today: 1.  In order to avoid problems such as
mail loops between email robots, we will not be sending you any
further responses today.  Please try again tomorrow.

If you believe this message is in error, or if you have any questions,
please contact the list owner at test-owner@example.com.""")


class TestHoldChain(unittest.TestCase):
    """Test the hold chain code."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._user_manager = getUtility(IUserManager)

    def test_hold_chain(self):
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        msgdata = dict(moderation_reasons=[
            'TEST-REASON-1',
            'TEST-REASON-2',
            ])
        logfile = LogFileMark('mailman.vette')
        process_chain(self._mlist, msg, msgdata, start_chain='hold')
        messages = get_queue_messages('virgin', expected_count=2)
        payloads = {}
        for item in messages:
            if item.msg['to'] == 'test-owner@example.com':
                part = item.msg.get_payload(0)
                payloads['owner'] = part.get_payload().splitlines()
            elif item.msg['To'] == 'anne@example.com':
                payloads['sender'] = item.msg.get_payload().splitlines()
            else:
                self.fail('Unexpected message: %s' % item.msg)
        self.assertIn('    TEST-REASON-1', payloads['owner'])
        self.assertIn('    TEST-REASON-2', payloads['owner'])
        self.assertIn('    TEST-REASON-1', payloads['sender'])
        self.assertIn('    TEST-REASON-2', payloads['sender'])
        logged = logfile.read()
        self.assertIn('TEST-REASON-1', logged)
        self.assertIn('TEST-REASON-2', logged)
        # Check the reason passed to hold_message().
        requests = IListRequests(self._mlist)
        self.assertEqual(requests.count_of(RequestType.held_message), 1)
        request = requests.of_type(RequestType.held_message)[0]
        key, data = requests.get_request(request.id)
        self.assertEqual(
            data.get('_mod_reason'), 'TEST-REASON-1; TEST-REASON-2')

    def test_hold_chain_no_reasons_given(self):
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        process_chain(self._mlist, msg, {}, start_chain='hold')
        # No reason was given, so a default is used.
        requests = IListRequests(self._mlist)
        self.assertEqual(requests.count_of(RequestType.held_message), 1)
        request = requests.of_type(RequestType.held_message)[0]
        key, data = requests.get_request(request.id)
        self.assertEqual(data.get('_mod_reason'), 'n/a')

    def test_hold_chain_charset(self):
        # Issue #144 - UnicodeEncodeError in the hold chain.
        self._mlist.admin_immed_notify = True
        self._mlist.respond_to_post_requests = False
        bart = self._user_manager.create_user('bart@example.com', 'Bart User')
        address = set_preferred(bart)
        self._mlist.subscribe(address, MemberRole.moderator)
        path = resource_filename('mailman.chains.tests', 'issue144.eml')
        with open(path, 'rb') as fp:
            msg = mfb(fp.read())
        msg.sender = 'anne@example.com'
        process_chain(self._mlist, msg, {}, start_chain='hold')
        # The postauth.txt message is now in the virgin queue awaiting
        # delivery to the moderators.
        items = get_queue_messages('virgin', expected_count=1)
        msgdata = items[0].msgdata
        # Should get sent to -owner address.
        self.assertEqual(msgdata['recipients'], {'test-owner@example.com'})
        # Ensure that the subject looks correct in the postauth.txt.
        msg = items[0].msg
        value = None
        for line in msg.get_payload(0).get_payload().splitlines():
            if line.strip().startswith('Subject:'):
                header, colon, value = line.partition(':')
                break
        self.assertEqual(value.lstrip(), 'Vi?enamjenski pi?tolj za vodu 8/1')
        self.assertEqual(
            msg['Subject'],
            'test@example.com post from anne@example.com requires approval')

    def test_hold_chain_crosspost(self):
        mlist2 = create_list('test2@example.com')
        msg = mfs("""\
From: anne@example.com
To: test@example.com, test2@example.com
Subject: A message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        process_chain(self._mlist, msg, {}, start_chain='hold')
        process_chain(mlist2, msg, {}, start_chain='hold')
        # There are four items in the virgin queue.  Two of them are for the
        # list owners who need to moderate the held message, and the other is
        # for anne telling her that her message was held for approval.
        items = get_queue_messages('virgin', expected_count=4)
        anne_froms = set()
        owner_tos = set()
        for item in items:
            if item.msg['to'] == 'anne@example.com':
                anne_froms.add(item.msg['from'])
            else:
                owner_tos.add(item.msg['to'])
        self.assertEqual(anne_froms, set(['test-bounces@example.com',
                                          'test2-bounces@example.com']))
        self.assertEqual(owner_tos, set(['test-owner@example.com',
                                         'test2-owner@example.com']))
        # And the message appears in the store.
        messages = list(getUtility(IMessageStore).messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['message-id'], '<ant>')
