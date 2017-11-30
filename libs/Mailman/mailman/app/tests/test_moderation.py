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

"""Moderation tests."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.app.moderator import (
    handle_message, handle_unsubscription, hold_message, hold_unsubscription)
from mailman.interfaces.action import Action
from mailman.interfaces.member import MemberRole
from mailman.interfaces.messages import IMessageStore
from mailman.interfaces.requests import IListRequests
from mailman.interfaces.subscriptions import ISubscriptionManager
from mailman.interfaces.usermanager import IUserManager
from mailman.runners.incoming import IncomingRunner
from mailman.runners.outgoing import OutgoingRunner
from mailman.runners.pipeline import PipelineRunner
from mailman.testing.helpers import (
    get_queue_messages, make_testable_runner, set_preferred,
    specialized_message_from_string as mfs)
from mailman.testing.layers import SMTPLayer
from mailman.utilities.datetime import now
from zope.component import getUtility


class TestModeration(unittest.TestCase):
    """Test moderation functionality."""

    layer = SMTPLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._request_db = IListRequests(self._mlist)
        self._msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: hold me
Message-ID: <alpha>

""")
        self._in = make_testable_runner(IncomingRunner, 'in')
        self._pipeline = make_testable_runner(PipelineRunner, 'pipeline')
        self._out = make_testable_runner(OutgoingRunner, 'out')

    def test_accepted_message_gets_posted(self):
        # A message that is accepted by the moderator should get posted to the
        # mailing list.  LP: #827697
        msgdata = dict(listname='test@example.com',
                       recipients=['bart@example.com'])
        request_id = hold_message(self._mlist, self._msg, msgdata)
        handle_message(self._mlist, request_id, Action.accept)
        self._in.run()
        self._pipeline.run()
        self._out.run()
        messages = list(SMTPLayer.smtpd.messages)
        self.assertEqual(len(messages), 1)
        message = messages[0]
        # We don't need to test the entire posted message, just the bits that
        # prove it got sent out.
        self.assertIn('x-mailman-version', message)
        self.assertIn('x-peer', message)
        # The X-Mailman-Approved-At header has local timezone information in
        # it, so test that separately.
        self.assertEqual(message['x-mailman-approved-at'][:-5],
                         'Mon, 01 Aug 2005 07:49:23 ')
        del message['x-mailman-approved-at']
        # The Message-ID matches the original.
        self.assertEqual(message['message-id'], '<alpha>')
        # Anne sent the message and the mailing list received it.
        self.assertEqual(message['from'], 'anne@example.com')
        self.assertEqual(message['to'], 'test@example.com')
        # The Subject header has the list's prefix.
        self.assertEqual(message['subject'], '[Test] hold me')
        # The list's -bounce address is the actual sender, and Bart is the
        # only actual recipient.  These headers are added by the testing
        # framework and don't show up in production.  They match the RFC 5321
        # envelope.
        self.assertEqual(message['x-mailfrom'], 'test-bounces@example.com')
        self.assertEqual(message['x-rcptto'], 'bart@example.com')

    def test_hold_action_alias_for_defer(self):
        # In handle_message(), the 'hold' action is the same as 'defer' for
        # purposes of this API.
        request_id = hold_message(self._mlist, self._msg)
        handle_message(self._mlist, request_id, Action.defer)
        # The message is still in the pending requests.
        key, data = self._request_db.get_request(request_id)
        self.assertEqual(key, '<alpha>')
        handle_message(self._mlist, request_id, Action.hold)
        key, data = self._request_db.get_request(request_id)
        self.assertEqual(key, '<alpha>')

    def test_lp_1031391(self):
        # LP: #1031391 msgdata['received_time'] gets added by the LMTP server.
        # The value is a datetime.  If this message gets held, it will break
        # pending requests since they require string keys and values.
        received_time = now()
        msgdata = dict(received_time=received_time)
        request_id = hold_message(self._mlist, self._msg, msgdata)
        key, data = self._request_db.get_request(request_id)
        self.assertEqual(data['received_time'], received_time)

    def test_forward(self):
        # We can forward the message to an email address.
        request_id = hold_message(self._mlist, self._msg)
        handle_message(self._mlist, request_id, Action.discard,
                       forward=['zack@example.com'])
        # The forwarded message lives in the virgin queue.
        items = get_queue_messages('virgin', expected_count=1)
        self.assertEqual(str(items[0].msg['subject']),
                         'Forward of moderated message')
        self.assertEqual(items[0].msgdata['recipients'],
                         ['zack@example.com'])

    def test_survive_a_deleted_message(self):
        # When the message that should be deleted is not found in the store,
        # no error is raised.
        request_id = hold_message(self._mlist, self._msg)
        message_store = getUtility(IMessageStore)
        message_store.delete_message('<alpha>')
        handle_message(self._mlist, request_id, Action.discard)
        self.assertEqual(self._request_db.count, 0)

    def test_handled_message_stays_in_store(self):
        # The message is still available in the store, even when it's been
        # disposed of.
        request_id = hold_message(self._mlist, self._msg)
        handle_message(self._mlist, request_id, Action.discard)
        self.assertEqual(self._request_db.count, 0)
        message = getUtility(IMessageStore).get_message_by_id('<alpha>')
        self.assertEqual(message['subject'], 'hold me')


class TestUnsubscription(unittest.TestCase):
    """Test unsubscription requests."""

    layer = SMTPLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._manager = ISubscriptionManager(self._mlist)

    def test_unsubscribe_defer(self):
        # When unsubscriptions must be approved by the moderator, but the
        # moderator defers this decision.
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_address('anne@example.org', 'Anne Person')
        token, token_owner, member = self._manager.register(
            anne, pre_verified=True, pre_confirmed=True, pre_approved=True)
        self.assertIsNone(token)
        self.assertEqual(member.address.email, 'anne@example.org')
        bart = user_manager.create_user('bart@example.com', 'Bart User')
        address = set_preferred(bart)
        self._mlist.subscribe(address, MemberRole.moderator)
        # Now hold and handle an unsubscription request.
        token = hold_unsubscription(self._mlist, 'anne@example.org')
        handle_unsubscription(self._mlist, token, Action.defer)
        items = get_queue_messages('virgin', expected_count=2)
        # Find the moderator message.
        for item in items:
            if item.msg['to'] == 'test-owner@example.com':
                break
        else:
            raise AssertionError('No moderator email found')
        self.assertEqual(
            item.msgdata['recipients'], {'test-owner@example.com'})
        self.assertEqual(
            item.msg['subject'],
            'New unsubscription request from Test by anne@example.org')

    def test_bogus_token(self):
        # Try to handle an unsubscription with a bogus token.
        self.assertRaises(LookupError, self._manager.confirm, None)
