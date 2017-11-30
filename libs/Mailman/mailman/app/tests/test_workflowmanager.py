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

"""Test email address registration."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.interfaces.mailinglist import SubscriptionPolicy
from mailman.interfaces.member import MemberRole
from mailman.interfaces.pending import IPendings
from mailman.interfaces.subscriptions import ISubscriptionManager, TokenOwner
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import get_queue_messages
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import now
from zope.component import getUtility


class TestRegistrar(unittest.TestCase):
    """Test registration."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._registrar = ISubscriptionManager(self._mlist)
        self._pendings = getUtility(IPendings)
        self._anne = getUtility(IUserManager).create_address(
            'anne@example.com')

    def test_initial_conditions(self):
        # Registering a subscription request provides a unique token associated
        # with a pendable, and the owner of the token.
        self.assertEqual(self._pendings.count, 0)
        token, token_owner, member = self._registrar.register(self._anne)
        self.assertIsNotNone(token)
        self.assertEqual(token_owner, TokenOwner.subscriber)
        self.assertIsNone(member)
        self.assertEqual(self._pendings.count, 1)
        record = self._pendings.confirm(token, expunge=False)
        self.assertEqual(record['list_id'], self._mlist.list_id)
        self.assertEqual(record['email'], 'anne@example.com')

    def test_subscribe(self):
        # Registering a subscription request where no confirmation or
        # moderation steps are needed, leaves us with no token or owner, since
        # there's nothing more to do.
        self._mlist.subscription_policy = SubscriptionPolicy.open
        self._anne.verified_on = now()
        token, token_owner, rmember = self._registrar.register(self._anne)
        self.assertIsNone(token)
        self.assertEqual(token_owner, TokenOwner.no_one)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertEqual(rmember, member)
        self.assertEqual(member.address, self._anne)
        # There's nothing to confirm.
        record = self._pendings.confirm(token, expunge=False)
        self.assertIsNone(record)

    def test_no_such_token(self):
        # Given a token which is not in the database, a LookupError is raised.
        self._registrar.register(self._anne)
        self.assertRaises(LookupError, self._registrar.confirm, 'not-a-token')

    def test_confirm_because_verify(self):
        # We have a subscription request which requires the user to confirm
        # (because she does not have a verified address), but not the moderator
        # to approve.  Running the workflow gives us a token.  Confirming the
        # token subscribes the user.
        self._mlist.subscription_policy = SubscriptionPolicy.open
        token, token_owner, rmember = self._registrar.register(self._anne)
        self.assertIsNotNone(token)
        self.assertEqual(token_owner, TokenOwner.subscriber)
        self.assertIsNone(rmember)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertIsNone(member)
        # Now confirm the subscription.
        token, token_owner, rmember = self._registrar.confirm(token)
        self.assertIsNone(token)
        self.assertEqual(token_owner, TokenOwner.no_one)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertEqual(rmember, member)
        self.assertEqual(member.address, self._anne)

    def test_confirm_because_confirm(self):
        # We have a subscription request which requires the user to confirm
        # (because of list policy), but not the moderator to approve.  Running
        # the workflow gives us a token.  Confirming the token subscribes the
        # user.
        self._mlist.subscription_policy = SubscriptionPolicy.confirm
        self._anne.verified_on = now()
        token, token_owner, rmember = self._registrar.register(self._anne)
        self.assertIsNotNone(token)
        self.assertEqual(token_owner, TokenOwner.subscriber)
        self.assertIsNone(rmember)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertIsNone(member)
        # Now confirm the subscription.
        token, token_owner, rmember = self._registrar.confirm(token)
        self.assertIsNone(token)
        self.assertEqual(token_owner, TokenOwner.no_one)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertEqual(rmember, member)
        self.assertEqual(member.address, self._anne)

    def test_confirm_because_moderation(self):
        # We have a subscription request which requires the moderator to
        # approve.  Running the workflow gives us a token.  Confirming the
        # token subscribes the user.
        self._mlist.subscription_policy = SubscriptionPolicy.moderate
        self._anne.verified_on = now()
        token, token_owner, rmember = self._registrar.register(self._anne)
        self.assertIsNotNone(token)
        self.assertEqual(token_owner, TokenOwner.moderator)
        self.assertIsNone(rmember)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertIsNone(member)
        # Now confirm the subscription.
        token, token_owner, rmember = self._registrar.confirm(token)
        self.assertIsNone(token)
        self.assertEqual(token_owner, TokenOwner.no_one)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertEqual(rmember, member)
        self.assertEqual(member.address, self._anne)

    def test_confirm_because_confirm_then_moderation(self):
        # We have a subscription request which requires the user to confirm
        # (because she does not have a verified address) and the moderator to
        # approve.  Running the workflow gives us a token.  Confirming the
        # token runs the workflow a little farther, but still gives us a
        # token.  Confirming again subscribes the user.
        self._mlist.subscription_policy = (
            SubscriptionPolicy.confirm_then_moderate)
        self._anne.verified_on = now()
        # Runs until subscription confirmation.
        token, token_owner, rmember = self._registrar.register(self._anne)
        self.assertIsNotNone(token)
        self.assertEqual(token_owner, TokenOwner.subscriber)
        self.assertIsNone(rmember)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertIsNone(member)
        # Now confirm the subscription, and wait for the moderator to approve
        # the subscription.  She is still not subscribed.
        new_token, token_owner, rmember = self._registrar.confirm(token)
        # The new token, used for the moderator to approve the message, is not
        # the same as the old token.
        self.assertNotEqual(new_token, token)
        self.assertIsNotNone(new_token)
        self.assertEqual(token_owner, TokenOwner.moderator)
        self.assertIsNone(rmember)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertIsNone(member)
        # Confirm once more, this time as the moderator approving the
        # subscription.  Now she's a member.
        token, token_owner, rmember = self._registrar.confirm(new_token)
        self.assertIsNone(token)
        self.assertEqual(token_owner, TokenOwner.no_one)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertEqual(rmember, member)
        self.assertEqual(member.address, self._anne)

    def test_confirm_then_moderate_with_different_tokens(self):
        # Ensure that the confirmation token the user sees when they have to
        # confirm their subscription is different than the token the moderator
        # sees when they approve the subscription.  This prevents the user
        # from using a replay attack to subvert moderator approval.
        self._mlist.subscription_policy = (
            SubscriptionPolicy.confirm_then_moderate)
        self._anne.verified_on = now()
        # Runs until subscription confirmation.
        token, token_owner, rmember = self._registrar.register(self._anne)
        self.assertIsNotNone(token)
        self.assertEqual(token_owner, TokenOwner.subscriber)
        self.assertIsNone(rmember)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertIsNone(member)
        # Now confirm the subscription, and wait for the moderator to approve
        # the subscription.  She is still not subscribed.
        new_token, token_owner, rmember = self._registrar.confirm(token)
        # The status is not true because the user has not yet been subscribed
        # to the mailing list.
        self.assertIsNotNone(new_token)
        self.assertEqual(token_owner, TokenOwner.moderator)
        self.assertIsNone(rmember)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertIsNone(member)
        # The new token is different than the old token.
        self.assertNotEqual(token, new_token)
        # Trying to confirm with the old token does not work.
        self.assertRaises(LookupError, self._registrar.confirm, token)
        # Confirm once more, this time with the new token, as the moderator
        # approving the subscription.  Now she's a member.
        done_token, token_owner, rmember = self._registrar.confirm(new_token)
        # The token is None, signifying that the member has been subscribed.
        self.assertIsNone(done_token)
        self.assertEqual(token_owner, TokenOwner.no_one)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertEqual(rmember, member)
        self.assertEqual(member.address, self._anne)

    def test_discard_waiting_for_confirmation(self):
        # While waiting for a user to confirm their subscription, we discard
        # the workflow.
        self._mlist.subscription_policy = SubscriptionPolicy.confirm
        self._anne.verified_on = now()
        # Runs until subscription confirmation.
        token, token_owner, rmember = self._registrar.register(self._anne)
        self.assertIsNotNone(token)
        self.assertEqual(token_owner, TokenOwner.subscriber)
        self.assertIsNone(rmember)
        member = self._mlist.regular_members.get_member('anne@example.com')
        self.assertIsNone(member)
        # Now discard the subscription request.
        self._registrar.discard(token)
        # Trying to confirm the token now results in an exception.
        self.assertRaises(LookupError, self._registrar.confirm, token)

    def test_admin_notify_mchanges(self):
        # When a user gets subscribed via the subscription policy workflow,
        # the list administrators get an email notification.
        self._mlist.subscription_policy = SubscriptionPolicy.open
        self._mlist.admin_notify_mchanges = True
        self._mlist.send_welcome_message = False
        token, token_owner, member = self._registrar.register(
            self._anne, pre_verified=True)
        # Anne is now a member.
        self.assertEqual(member.address.email, 'anne@example.com')
        # And there's a notification email waiting for Bart.
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['To'], 'ant-owner@example.com')
        self.assertEqual(message['Subject'], 'Ant subscription notification')
        self.assertEqual(message.get_payload(), """\
anne@example.com has been successfully subscribed to Ant.
""")

    def test_no_admin_notify_mchanges(self):
        # Even when a user gets subscribed via the subscription policy
        # workflow, the list administrators won't get an email notification if
        # they don't want one.
        self._mlist.subscription_policy = SubscriptionPolicy.open
        self._mlist.admin_notify_mchanges = False
        self._mlist.send_welcome_message = False
        # Bart is an administrator of the mailing list.
        bart = getUtility(IUserManager).create_address(
            'bart@example.com', 'Bart Person')
        self._mlist.subscribe(bart, MemberRole.owner)
        token, token_owner, member = self._registrar.register(
            self._anne, pre_verified=True)
        # Anne is now a member.
        self.assertEqual(member.address.email, 'anne@example.com')
        # There's no notification email waiting for Bart.
        get_queue_messages('virgin', expected_count=0)
