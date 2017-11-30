# Copyright (C) 2014-2017 by the Free Software Foundation, Inc.
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

"""Test the `member-moderation` and `nonmember-moderation` rules."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.interfaces.action import Action
from mailman.interfaces.bans import IBanManager
from mailman.interfaces.member import MemberRole
from mailman.interfaces.usermanager import IUserManager
from mailman.rules import moderation
from mailman.testing.helpers import (
    set_preferred, specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestModeration(unittest.TestCase):
    """Test the approved handler."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')

    def test_member_and_nonmember(self):
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_address('anne@example.com')
        user_manager.create_address('bill@example.com')
        self._mlist.subscribe(anne, MemberRole.member)
        rule = moderation.NonmemberModeration()
        msg = mfs("""\
From: anne@example.com
Sender: bill@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        # Both Anne and Bill are in the message's senders list.
        self.assertIn('anne@example.com', msg.senders)
        self.assertIn('bill@example.com', msg.senders)
        # The NonmemberModeration rule should *not* hit, because even though
        # Bill is in the list of senders he is not a member of the mailing
        # list.  Anne is also in the list of senders and she *is* a member, so
        # she takes precedence.
        result = rule.check(self._mlist, msg, {})
        self.assertFalse(result, 'NonmemberModeration rule should not hit')
        # After the rule runs, Bill becomes a non-member.
        bill_member = self._mlist.nonmembers.get_member('bill@example.com')
        self.assertIsNotNone(bill_member)
        # Bill is not a member.
        bill_member = self._mlist.members.get_member('bill@example.com')
        self.assertIsNone(bill_member)

    def test_moderation_reason(self):
        # When a message is moderated, a reason is added to the metadata.
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_address('anne@example.com')
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        # Anne is in the message's senders list.
        self.assertIn('anne@example.com', msg.senders)
        # Now run the rule.
        rule = moderation.NonmemberModeration()
        msgdata = {}
        result = rule.check(self._mlist, msg, msgdata)
        self.assertTrue(result, 'NonmemberModeration rule should hit')
        # The reason for moderation should be in the msgdata.
        reasons = msgdata['moderation_reasons']
        self.assertEqual(reasons, ['The message is not from a list member'])
        # Now make Anne a moderated member...
        anne_member = self._mlist.subscribe(anne, MemberRole.member)
        anne_member.moderation_action = Action.hold
        # ...and run the rule again.
        rule = moderation.MemberModeration()
        msgdata = {}
        result = rule.check(self._mlist, msg, msgdata)
        self.assertTrue(result, 'MemberModeration rule should hit')
        # The reason for moderation should be in the msgdata.
        reasons = msgdata['moderation_reasons']
        self.assertEqual(
            reasons, ['The message comes from a moderated member'])

    def test_these_nonmembers(self):
        # Test the legacy *_these_nonmembers attributes.
        user_manager = getUtility(IUserManager)
        actions = {
            'anne@example.com': 'accept',
            'bill@example.com': 'hold',
            'chris@example.com': 'reject',
            'dana@example.com': 'discard',
            '^anne-.*@example.com': 'accept',
            '^bill-.*@example.com': 'hold',
            '^chris-.*@example.com': 'reject',
            '^dana-.*@example.com': 'discard',
            }
        rule = moderation.NonmemberModeration()
        user_manager = getUtility(IUserManager)
        for address, action_name in actions.items():
            setattr(self._mlist,
                    '{}_these_nonmembers'.format(action_name),
                    [address])
            if address.startswith('^'):
                # It's a pattern, craft a proper address.
                address = address[1:].replace('.*', 'something')
            user_manager.create_address(address)
            msg = mfs("""\
From: {}
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""".format(address))
            msgdata = {}
            result = rule.check(self._mlist, msg, msgdata)
            self.assertTrue(result, 'NonmemberModeration rule should hit')
            self.assertIn('moderation_action', msgdata)
            self.assertEqual(
                msgdata['moderation_action'], action_name,
                'Wrong action for {}: {}'.format(address, action_name))

    def test_nonmember_fallback_to_list_defaults(self):
        # https://gitlab.com/mailman/mailman/issues/189
        self._mlist.default_nonmember_action = Action.hold
        user_manager = getUtility(IUserManager)
        user_manager.create_address('anne@example.com')
        rule = moderation.NonmemberModeration()
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        # First, the message should get held.
        msgdata = {}
        result = rule.check(self._mlist, msg, msgdata)
        self.assertTrue(result)
        self.assertEqual(msgdata['moderation_action'], 'hold')
        # As a side-effect, Anne has been added as a nonmember with a
        # moderation action that falls back to the list's default.
        anne = self._mlist.nonmembers.get_member('anne@example.com')
        self.assertIsNone(anne.moderation_action)
        # Then the list's default nonmember action is changed.
        self._mlist.default_nonmember_action = Action.discard
        msg.replace_header('Message-ID', '<bee>')
        # This time, the message should be discarded.
        result = rule.check(self._mlist, msg, msgdata)
        self.assertTrue(result)
        self.assertEqual(msgdata.get('moderation_action'), 'discard')

    def test_member_fallback_to_list_defaults(self):
        # https://gitlab.com/mailman/mailman/issues/189
        self._mlist.default_member_action = Action.accept
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_address('anne@example.com')
        member = self._mlist.subscribe(anne, MemberRole.member)
        # Anne's moderation rule falls back to the list default.
        self.assertIsNone(member.moderation_action)
        rule = moderation.MemberModeration()
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        # First, the message gets accepted.
        msgdata = {}
        result = rule.check(self._mlist, msg, msgdata)
        self.assertTrue(result)
        self.assertEqual(msgdata.get('moderation_action'), 'accept')
        # Then the list's default member action is changed.
        self._mlist.default_member_action = Action.hold
        msg.replace_header('Message-ID', '<bee>')
        # This time, the message is held.
        result = rule.check(self._mlist, msg, msgdata)
        self.assertTrue(result)
        self.assertEqual(msgdata.get('moderation_action'), 'hold')

    def test_linked_address_nonmembermoderation_misses(self):
        # Anne subscribes to a mailing list as a user with her preferred
        # address.  She also has a secondary linked address, and she uses this
        # to post to the mailing list.  The NonmemberModeration rule misses
        # because Anne is not a nonmember.
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_user('anne@example.com')
        set_preferred(anne)
        self._mlist.subscribe(anne, MemberRole.member)
        anne.link(user_manager.create_address('anne.person@example.com'))
        rule = moderation.NonmemberModeration()
        msg = mfs("""\
From: anne.person@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        result = rule.check(self._mlist, msg, {})
        self.assertFalse(result)

    def test_linked_address_membermoderation_hits(self):
        # Anne subscribes to a mailing list as a user with her preferred
        # address.  She also has a secondary linked address, and she uses this
        # to post to the mailing list.  The MemberModeration rule hits because
        # Anne is a member.
        self._mlist.default_member_action = Action.accept
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_user('anne@example.com')
        set_preferred(anne)
        self._mlist.subscribe(anne, MemberRole.member)
        anne.link(user_manager.create_address('anne.person@example.com'))
        rule = moderation.MemberModeration()
        msg = mfs("""\
From: anne.person@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        result = rule.check(self._mlist, msg, {})
        self.assertTrue(result)

    def test_banned_address_linked_to_user(self):
        # Anne is subscribed to a mailing list as a user with her preferred
        # address.  She also has a secondary address which is banned and which
        # she uses to post to the mailing list.  Both the MemberModeration and
        # NonmemberModeration rules miss because the posting address is
        # banned.
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_user('anne@example.com')
        set_preferred(anne)
        self._mlist.subscribe(anne, MemberRole.member)
        anne.link(user_manager.create_address('anne.person@example.com'))
        IBanManager(self._mlist).ban('anne.person@example.com')
        msg = mfs("""\
From: anne.person@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        rule = moderation.MemberModeration()
        result = rule.check(self._mlist, msg, {})
        self.assertFalse(result)
        rule = moderation.NonmemberModeration()
        result = rule.check(self._mlist, msg, {})
        self.assertFalse(result)

    def test_banned_sender_among_multiple_senders(self):
        # Two addresses are created, one of which is banned.  Even though the
        # The Nonmember moderation rule misses if any of the banned addresses
        # appear in the 'senders' headers of the message.
        user_manager = getUtility(IUserManager)
        user_manager.create_address('anne@example.com')
        user_manager.create_address('bart@example.com')
        IBanManager(self._mlist).ban('bart@example.com')
        rule = moderation.NonmemberModeration()
        msg = mfs("""\
From: anne@example.com
Sender: bart@example.com
To: test@example.com
Subject: A test message
Message-ID: <ant>
MIME-Version: 1.0

A message body.
""")
        result = rule.check(self._mlist, msg, {})
        self.assertFalse(result)
