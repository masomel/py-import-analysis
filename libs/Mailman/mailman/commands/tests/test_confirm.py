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

"""Test the `confirm` command."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.commands.eml_confirm import Confirm
from mailman.config import config
from mailman.email.message import Message
from mailman.interfaces.command import ContinueProcessing
from mailman.interfaces.mailinglist import SubscriptionPolicy
from mailman.interfaces.subscriptions import ISubscriptionManager
from mailman.interfaces.usermanager import IUserManager
from mailman.runners.command import CommandRunner, Results
from mailman.testing.helpers import (
    get_queue_messages, make_testable_runner,
    specialized_message_from_string as mfs, subscribe)
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestConfirmJoin(unittest.TestCase):
    """Test the `confirm` command when joining a mailing list."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        anne = getUtility(IUserManager).create_address(
            'anne@example.com', 'Anne Person')
        self._token, token_owner, member = ISubscriptionManager(
            self._mlist).register(anne)
        self._command = Confirm()
        # Clear the virgin queue.
        get_queue_messages('virgin')

    def test_welcome_message(self):
        # A confirmation causes a welcome message to be sent to the member, if
        # enabled by the mailing list.
        status = self._command.process(
            self._mlist, Message(), {}, (self._token,), Results())
        self.assertEqual(status, ContinueProcessing.yes)
        # There should be one messages in the queue; the welcome message.
        items = get_queue_messages('virgin', expected_count=1)
        # Grab the welcome message.
        welcome = items[0].msg
        self.assertEqual(welcome['subject'],
                         'Welcome to the "Test" mailing list')
        self.assertEqual(welcome['to'], 'Anne Person <anne@example.com>')

    def test_no_welcome_message(self):
        # When configured not to send a welcome message, none is sent.
        self._mlist.send_welcome_message = False
        status = self._command.process(
            self._mlist, Message(), {}, (self._token,), Results())
        self.assertEqual(status, ContinueProcessing.yes)
        # There will be no messages in the queue.
        get_queue_messages('virgin', expected_count=0)


class TestConfirmLeave(unittest.TestCase):
    """Test the `confirm` command when leaving a mailing list."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        anne = subscribe(self._mlist, 'Anne', email='anne@example.com')
        self._token, token_owner, member = ISubscriptionManager(
            self._mlist).unregister(anne.address)

    def test_confirm_leave(self):
        msg = mfs("""\
From: Anne Person <anne@example.com>
To: test-confirm+{token}@example.com
Subject: Re: confirm {token}

""".format(token=self._token))
        Confirm().process(self._mlist, msg, {}, (self._token,), Results())
        # Anne is no longer a member of the mailing list.
        member = self._mlist.members.get_member('anne@example.com')
        self.assertIsNone(member)


class TestEmailResponses(unittest.TestCase):
    """Test the `confirm` command through the command runner."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')

    def test_confirm_then_moderate_workflow(self):
        # Issue #114 describes a problem when confirming the moderation email.
        self._mlist.subscription_policy = (
            SubscriptionPolicy.confirm_then_moderate)
        bart = getUtility(IUserManager).create_address(
            'bart@example.com', 'Bart Person')
        # Clear any previously queued confirmation messages.
        get_queue_messages('virgin')
        self._token, token_owner, member = ISubscriptionManager(
            self._mlist).register(bart)
        # There should now be one email message in the virgin queue, i.e. the
        # confirmation message sent to Bart.
        items = get_queue_messages('virgin', expected_count=1)
        msg = items[0].msg
        # Confirmations come first, so this one goes to the subscriber.
        self.assertEqual(msg['to'], 'bart@example.com')
        confirm, token = str(msg['subject']).split()
        self.assertEqual(confirm, 'confirm')
        self.assertEqual(token, self._token)
        # Craft a confirmation response with the expected tokens.
        user_response = Message()
        user_response['From'] = 'bart@example.com'
        user_response['To'] = 'test-confirm+{}@example.com'.format(token)
        user_response['Subject'] = 'Re: confirm {}'.format(token)
        user_response.set_payload('')
        # Process the message through the command runner.
        config.switchboards['command'].enqueue(
            user_response, listid='test.example.com')
        make_testable_runner(CommandRunner, 'command').run()
        # There are now two messages in the virgin queue.  One is going to the
        # subscriber containing the results of their confirmation message, and
        # the other is to the moderators informing them that they need to
        # handle the moderation queue.
        items = get_queue_messages('virgin', expected_count=2)
        if items[0].msg['to'] == 'bart@example.com':
            results = items[0].msg
            moderator_msg = items[1].msg
        else:
            results = items[1].msg
            moderator_msg = items[0].msg
        # Check the moderator message first.
        self.assertEqual(moderator_msg['to'], 'test-owner@example.com')
        self.assertEqual(
            moderator_msg['subject'],
            'New subscription request to Test from bart@example.com')
        lines = moderator_msg.get_payload().splitlines()
        self.assertEqual(
            lines[-2].strip(),
            'For:  Bart Person <bart@example.com>')
        self.assertEqual(lines[-1].strip(), 'List: test@example.com')
        # Now check the results message.
        self.assertEqual(
            str(results['subject']), 'The results of your email commands')
        self.assertMultiLineEqual(results.get_payload(), """\
The results of your email command are provided below.

- Original message details:
From: bart@example.com
Subject: Re: confirm {}
Date: n/a
Message-ID: n/a

- Results:
Confirmed

- Done.
""".format(token))
