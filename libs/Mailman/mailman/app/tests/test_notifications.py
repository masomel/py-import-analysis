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

"""Test notifications."""

import os
import unittest

from contextlib import ExitStack
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.interfaces.languages import ILanguageManager
from mailman.interfaces.member import MemberRole
from mailman.interfaces.template import ITemplateManager
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import (
    get_queue_messages, set_preferred, subscribe)
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import now
from tempfile import TemporaryDirectory
from zope.component import getUtility


class TestNotifications(unittest.TestCase):
    """Test notifications."""

    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        resources = ExitStack()
        self.addCleanup(resources.close)
        self.var_dir = resources.enter_context(TemporaryDirectory())
        self._mlist = create_list('test@example.com')
        self._mlist.display_name = 'Test List'
        getUtility(ITemplateManager).set(
            'list:user:notice:welcome', self._mlist.list_id,
            'mailman:///welcome.txt')
        config.push('template config', """\
        [paths.testing]
        template_dir: {}/templates
        """.format(self.var_dir))
        resources.callback(config.pop, 'template config')
        # Populate the template directories with a few fake templates.
        path = os.path.join(self.var_dir, 'templates', 'site', 'en')
        os.makedirs(path)
        full_path = os.path.join(path, 'list:user:notice:welcome.txt')
        with open(full_path, 'w', encoding='utf-8') as fp:
            print("""\
Welcome to the $list_name mailing list.

    Posting address: $fqdn_listname
    Help and other requests: $list_requests
    Your name: $user_name
    Your address: $user_address""", file=fp)
        # Write a list-specific welcome message.
        path = os.path.join(self.var_dir, 'templates', 'lists',
                            'test@example.com', 'xx')
        os.makedirs(path)
        full_path = os.path.join(path, 'list:user:notice:welcome.txt')
        with open(full_path, 'w', encoding='utf-8') as fp:
            print('You just joined the $list_name mailing list!', file=fp)

    def test_welcome_message(self):
        subscribe(self._mlist, 'Anne', email='anne@example.com')
        # Now there's one message in the virgin queue.
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(str(message['subject']),
                         'Welcome to the "Test List" mailing list')
        self.assertMultiLineEqual(message.get_payload(), """\
Welcome to the Test List mailing list.

    Posting address: test@example.com
    Help and other requests: test-request@example.com
    Your name: Anne Person
    Your address: anne@example.com
""")

    def test_more_specific_welcome_message_nonenglish(self):
        # The welcome message url can contain placeholders for the fqdn list
        # name and language.
        getUtility(ITemplateManager).set(
            'list:user:notice:welcome', self._mlist.list_id,
            'mailman:///$listname/$language/welcome.txt')
        # Add the xx language and subscribe Anne using it.
        manager = getUtility(ILanguageManager)
        manager.add('xx', 'us-ascii', 'Xlandia')
        # We can't use the subscribe() helper because that would send the
        # welcome message before we set the member's preferred language.
        address = getUtility(IUserManager).create_address(
            'anne@example.com', 'Anne Person')
        address.preferences.preferred_language = 'xx'
        self._mlist.subscribe(address)
        # Now there's one message in the virgin queue.
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(str(message['subject']),
                         'Welcome to the "Test List" mailing list')
        self.assertMultiLineEqual(
            message.get_payload(),
            'You just joined the Test List mailing list!')

    def test_no_welcome_message_to_owners(self):
        # Welcome messages go only to mailing list members, not to owners.
        subscribe(self._mlist, 'Anne', MemberRole.owner, 'anne@example.com')
        # There is no welcome message in the virgin queue.
        get_queue_messages('virgin', expected_count=0)

    def test_no_welcome_message_to_nonmembers(self):
        # Welcome messages go only to mailing list members, not to nonmembers.
        subscribe(self._mlist, 'Anne', MemberRole.nonmember,
                  'anne@example.com')
        # There is no welcome message in the virgin queue.
        get_queue_messages('virgin', expected_count=0)

    def test_no_welcome_message_to_moderators(self):
        # Welcome messages go only to mailing list members, not to moderators.
        subscribe(self._mlist, 'Anne', MemberRole.moderator,
                  'anne@example.com')
        # There is no welcome message in the virgin queue.
        get_queue_messages('virgin', expected_count=0)

    def test_member_susbcribed_address_has_display_name(self):
        address = getUtility(IUserManager).create_address(
            'anne@example.com', 'Anne Person')
        address.verified_on = now()
        self._mlist.subscribe(address)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['to'], 'Anne Person <anne@example.com>')

    def test_member_subscribed_address_has_no_display_name(self):
        address = getUtility(IUserManager).create_address('anne@example.com')
        address.verified_on = now()
        self._mlist.subscribe(address)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['to'], 'anne@example.com')

    def test_member_is_user_and_has_display_name(self):
        user = getUtility(IUserManager).create_user(
            'anne@example.com', 'Anne Person')
        set_preferred(user)
        self._mlist.subscribe(user)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['to'], 'Anne Person <anne@example.com>')

    def test_member_is_user_and_has_no_display_name(self):
        user = getUtility(IUserManager).create_user('anne@example.com')
        set_preferred(user)
        self._mlist.subscribe(user)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['to'], 'anne@example.com')

    def test_member_has_linked_user_display_name(self):
        user = getUtility(IUserManager).create_user(
            'anne@example.com', 'Anne Person')
        set_preferred(user)
        address = getUtility(IUserManager).create_address('anne2@example.com')
        address.verified_on = now()
        user.link(address)
        self._mlist.subscribe(address)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['to'], 'Anne Person <anne2@example.com>')

    def test_member_has_no_linked_display_name(self):
        user = getUtility(IUserManager).create_user('anne@example.com')
        set_preferred(user)
        address = getUtility(IUserManager).create_address('anne2@example.com')
        address.verified_on = now()
        user.link(address)
        self._mlist.subscribe(address)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['to'], 'anne2@example.com')

    def test_member_has_address_and_user_display_name(self):
        user = getUtility(IUserManager).create_user(
            'anne@example.com', 'Anne Person')
        set_preferred(user)
        address = getUtility(IUserManager).create_address(
            'anne2@example.com', 'Anne X Person')
        address.verified_on = now()
        user.link(address)
        self._mlist.subscribe(address)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['to'], 'Anne X Person <anne2@example.com>')
