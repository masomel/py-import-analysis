# Copyright (C) 2016-2017 by the Free Software Foundation, Inc.
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

"""Test for unsubscription service."""

import unittest

from contextlib import suppress
from mailman.app.lifecycle import create_list
from mailman.app.subscriptions import UnSubscriptionWorkflow
from mailman.interfaces.mailinglist import SubscriptionPolicy
from mailman.interfaces.pending import IPendings
from mailman.interfaces.subscriptions import TokenOwner
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import LogFileMark, get_queue_messages
from mailman.testing.layers import ConfigLayer
from mailman.utilities.datetime import now
from unittest.mock import patch
from zope.component import getUtility


class TestUnSubscriptionWorkflow(unittest.TestCase):
    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._mlist.admin_immed_notify = False
        self._mlist.unsubscription_policy = SubscriptionPolicy.open
        self._mlist.send_welcome_message = False
        self._anne = 'anne@example.com'
        self._user_manager = getUtility(IUserManager)
        self.anne = self._user_manager.create_user(self._anne)
        self.anne.addresses[0].verified_on = now()
        self.anne.preferred_address = self.anne.addresses[0]
        self._mlist.subscribe(self.anne)
        self._expected_pendings_count = 0

    def tearDown(self):
        # There usually should be no pending after all is said and done, but
        # some tests don't complete the workflow.
        self.assertEqual(getUtility(IPendings).count,
                         self._expected_pendings_count)

    def test_start_state(self):
        # Test the workflow starts with no tokens or members.
        workflow = UnSubscriptionWorkflow(self._mlist)
        self.assertEqual(workflow.token_owner, TokenOwner.no_one)
        self.assertIsNone(workflow.token)
        self.assertIsNone(workflow.member)

    def test_pended_data(self):
        # Test there is a Pendable object associated with a held
        # unsubscription request and it has some valid data associated with
        # it.
        self._mlist.unsubscription_policy = SubscriptionPolicy.confirm
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        with suppress(StopIteration):
            workflow.run_thru('send_confirmation')
        self.assertIsNotNone(workflow.token)
        pendable = getUtility(IPendings).confirm(workflow.token, expunge=False)
        self.assertEqual(pendable['list_id'], 'test.example.com')
        self.assertEqual(pendable['email'], 'anne@example.com')
        self.assertEqual(pendable['display_name'], '')
        self.assertEqual(pendable['when'], '2005-08-01T07:49:23')
        self.assertEqual(pendable['token_owner'], 'subscriber')
        # The token is still in the database.
        self._expected_pendings_count = 1

    def test_user_or_address_required(self):
        # The `subscriber` attribute must be a user or address that is provided
        # to the workflow.
        workflow = UnSubscriptionWorkflow(self._mlist)
        self.assertRaises(AssertionError, list, workflow)

    def test_user_is_subscribed_to_unsubscribe(self):
        # A user must be subscribed to a list when trying to unsubscribe.
        addr = self._user_manager.create_address('aperson@example.org')
        addr.verfied_on = now()
        workflow = UnSubscriptionWorkflow(self._mlist, addr)
        self.assertRaises(AssertionError,
                          workflow.run_thru, 'subscription_checks')

    def test_confirmation_checks_open_list(self):
        # An unsubscription from an open list does not need to be confirmed or
        # moderated.
        self._mlist.unsubscription_policy = SubscriptionPolicy.open
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        workflow.run_thru('confirmation_checks')
        with patch.object(workflow, '_step_do_unsubscription') as step:
            next(workflow)
        step.assert_called_once_with()

    def test_confirmation_checks_no_user_confirmation_needed(self):
        # An unsubscription from a list which does not need user confirmation
        # skips to the moderation checks.
        self._mlist.unsubscription_policy = SubscriptionPolicy.moderate
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne,
                                          pre_confirmed=True)
        workflow.run_thru('confirmation_checks')
        with patch.object(workflow, '_step_moderation_checks') as step:
            next(workflow)
        step.assert_called_once_with()

    def test_confirmation_checks_confirm_pre_confirmed(self):
        # The unsubscription policy requires user-confirmation, but their
        # unsubscription is pre-confirmed. Since moderation is not reuqired,
        # the user will be immediately unsubscribed.
        self._mlist.unsubscription_policy = SubscriptionPolicy.confirm
        workflow = UnSubscriptionWorkflow(
            self._mlist, self.anne, pre_confirmed=True)
        workflow.run_thru('confirmation_checks')
        with patch.object(workflow, '_step_do_unsubscription') as step:
            next(workflow)
        step.assert_called_once_with()

    def test_confirmation_checks_confirm_then_moderate_pre_confirmed(self):
        # The unsubscription policy requires user confirmation, but their
        # unsubscription is pre-confirmed. Since moderation is required, that
        # check will be performed.
        self._mlist.unsubscription_policy = (
            SubscriptionPolicy.confirm_then_moderate)
        workflow = UnSubscriptionWorkflow(
            self._mlist, self.anne, pre_confirmed=True)
        workflow.run_thru('confirmation_checks')
        with patch.object(workflow, '_step_do_unsubscription') as step:
            next(workflow)
        step.assert_called_once_with()

    def test_send_confirmation_checks_confirm_list(self):
        # The unsubscription policy requires user confirmation and the
        # unsubscription is not pre-confirmed.
        self._mlist.unsubscription_policy = SubscriptionPolicy.confirm
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        workflow.run_thru('confirmation_checks')
        with patch.object(workflow, '_step_send_confirmation') as step:
            next(workflow)
        step.assert_called_once_with()

    def test_moderation_checks_moderated_list(self):
        # The unsubscription policy requires moderation.
        self._mlist.unsubscription_policy = SubscriptionPolicy.moderate
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        workflow.run_thru('confirmation_checks')
        with patch.object(workflow, '_step_moderation_checks') as step:
            next(workflow)
            step.assert_called_once_with()

    def test_moderation_checks_approval_required(self):
        # The moderator must approve the subscription request.
        self._mlist.unsubscription_policy = SubscriptionPolicy.moderate
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        workflow.run_thru('moderation_checks')
        with patch.object(workflow, '_step_get_moderator_approval') as step:
            next(workflow)
        step.assert_called_once_with()

    def test_do_unsusbcription(self):
        # An open unsubscription policy means the user gets unsubscribed to
        # the mailing list without any further confirmations or approvals.
        self._mlist.unsubscription_policy = SubscriptionPolicy.open
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        list(workflow)
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNone(member)

    def test_do_unsubscription_pre_approved(self):
        # A moderation-requiring subscription policy plus a pre-approved
        # address means the user gets unsubscribed from the mailing list
        # without any further confirmation or approvals.
        self._mlist.unsubscription_policy = SubscriptionPolicy.moderate
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne,
                                          pre_approved=True)
        list(workflow)
        # Anne is now unsubscribed form the mailing list.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNone(member)
        # No further token is needed.
        self.assertIsNone(workflow.token)
        self.assertEqual(workflow.token_owner, TokenOwner.no_one)

    def test_do_unsubscription_pre_approved_pre_confirmed(self):
        # A moderation-requiring unsubscription policy plus a pre-appvoed
        # address means the user gets unsubscribed to the mailing list without
        # any further confirmations or approvals.
        self._mlist.unsubscription_policy = (
            SubscriptionPolicy.confirm_then_moderate)
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne,
                                          pre_approved=True,
                                          pre_confirmed=True)
        list(workflow)
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNone(member)
        # No further token is needed.
        self.assertIsNone(workflow.token)
        self.assertEqual(workflow.token_owner, TokenOwner.no_one)

    def test_do_unsubscription_cleanups(self):
        # Once the user is unsubscribed, the token and its associated pending
        # database record will be removed from the database.
        self._mlist.unsubscription_policy = SubscriptionPolicy.open
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne,
                                          pre_approved=True,
                                          pre_confirmed=True)
        # Run the workflow.
        list(workflow)
        # Anne is now unsubscribed from the list.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNone(member)
        # Workflow is done, so it has no token.
        self.assertIsNone(workflow.token)
        self.assertEqual(workflow.token_owner, TokenOwner.no_one)

    def test_moderator_approves(self):
        # The workflow runs until moderator approval is required, at which
        # point the workflow is saved.  Once the moderator approves, the
        # workflow resumes and the user is unsubscribed.
        self._mlist.unsubscription_policy = SubscriptionPolicy.moderate
        workflow = UnSubscriptionWorkflow(
            self._mlist, self.anne, pre_confirmed=True)
        # Run the entire workflow.
        list(workflow)
        # The user is currently subscribed to the mailing list.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNotNone(member)
        self.assertIsNotNone(workflow.member)
        # The token is owned by the moderator.
        self.assertIsNotNone(workflow.token)
        self.assertEqual(workflow.token_owner, TokenOwner.moderator)
        # Create a new workflow with the previous workflow's save token, and
        # restore its state.  This models an approved un-sunscription request
        # and should result in the user getting subscribed.
        approved_workflow = UnSubscriptionWorkflow(self._mlist)
        approved_workflow.token = workflow.token
        approved_workflow.restore()
        list(approved_workflow)
        # Now the user is unsubscribed from the mailing list.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNone(member)
        self.assertEqual(approved_workflow.member, member)
        # No further token is needed.
        self.assertIsNone(approved_workflow.token)
        self.assertEqual(approved_workflow.token_owner, TokenOwner.no_one)

    def test_get_moderator_approval_log_on_hold(self):
        # When the unsubscription is held for moderator approval, a message is
        # logged.
        mark = LogFileMark('mailman.subscribe')
        self._mlist.unsubscription_policy = SubscriptionPolicy.moderate
        workflow = UnSubscriptionWorkflow(
            self._mlist, self.anne, pre_confirmed=True)
        # Run the entire workflow.
        list(workflow)
        self.assertIn(
         'test@example.com: held unsubscription request from anne@example.com',
         mark.readline()
         )
        # The state machine stopped at the moderator approval step so there
        # will be one token still in the database.
        self._expected_pendings_count = 1

    def test_get_moderator_approval_notifies_moderators(self):
        # When the unsubscription is held for moderator approval, and the list
        # is so configured, a notification is sent to the list moderators.
        self._mlist.admin_immed_notify = True
        self._mlist.unsubscription_policy = SubscriptionPolicy.moderate
        workflow = UnSubscriptionWorkflow(
            self._mlist, self.anne, pre_confirmed=True)
        # Consume the entire state machine.
        list(workflow)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['From'], 'test-owner@example.com')
        self.assertEqual(message['To'], 'test-owner@example.com')
        self.assertEqual(
            message['Subject'],
            'New unsubscription request to Test from anne@example.com')
        self.assertEqual(message.get_payload(), """\
Your authorization is required for a mailing list unsubscription
request approval:

    For:  anne@example.com
    List: test@example.com
""")
        # The state machine stopped at the moderator approval so there will be
        # one token still in the database.
        self._expected_pendings_count = 1

    def test_get_moderator_approval_no_notifications(self):
        # When the unsubscription request is held for moderator approval, and
        # the list is so configured, a notification is sent to the list
        # moderators.
        self._mlist.admin_immed_notify = False
        self._mlist.unsubscription_policy = SubscriptionPolicy.moderate
        workflow = UnSubscriptionWorkflow(
            self._mlist, self.anne, pre_confirmed=True)
        # Consume the entire state machine.
        list(workflow)
        get_queue_messages('virgin', expected_count=0)
        # The state machine stopped at the moderator approval so there will be
        # one token still in the database.
        self._expected_pendings_count = 1

    def test_send_confirmation(self):
        # A confirmation message gets sent when the unsubscription must be
        # confirmed.
        self._mlist.unsubscription_policy = SubscriptionPolicy.confirm
        # Run the workflow to model the confirmation step.
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        list(workflow)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        token = workflow.token
        self.assertEqual(
            message['Subject'], 'confirm {}'.format(workflow.token))
        self.assertEqual(
            message['From'], 'test-confirm+{}@example.com'.format(token))
        # The state machine stopped at the member confirmation step so there
        # will be one token still in the database.
        self._expected_pendings_count = 1

    def test_do_confirmation_unsubscribes_user(self):
        # Unsubscriptions to the mailing list must be confirmed.  Once that's
        # done, the user's address is unsubscribed.
        self._mlist.unsubscription_policy = SubscriptionPolicy.confirm
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        list(workflow)
        # Anne is a member.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNotNone(member)
        self.assertEqual(member, workflow.member)
        # The token is owned by the subscriber.
        self.assertIsNotNone(workflow.token)
        self.assertEqual(workflow.token_owner, TokenOwner.subscriber)
        # Confirm.
        confirm_workflow = UnSubscriptionWorkflow(self._mlist)
        confirm_workflow.token = workflow.token
        confirm_workflow.restore()
        list(confirm_workflow)
        # Anne is now unsubscribed.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNone(member)
        # No further token is needed.
        self.assertIsNone(confirm_workflow.token)
        self.assertEqual(confirm_workflow.token_owner, TokenOwner.no_one)

    def test_do_confirmation_unsubscribes_address(self):
        # Unsubscriptions to the mailing list must be confirmed.  Once that's
        # done, the address is unsubscribed.
        address = self.anne.register('anne.person@example.com')
        self._mlist.subscribe(address)
        self._mlist.unsubscription_policy = SubscriptionPolicy.confirm
        workflow = UnSubscriptionWorkflow(self._mlist, address)
        list(workflow)
        # Bart is a member.
        member = self._mlist.regular_members.get_member(
            'anne.person@example.com')
        self.assertIsNotNone(member)
        self.assertEqual(member, workflow.member)
        # The token is owned by the subscriber.
        self.assertIsNotNone(workflow.token)
        self.assertEqual(workflow.token_owner, TokenOwner.subscriber)
        # Confirm.
        confirm_workflow = UnSubscriptionWorkflow(self._mlist)
        confirm_workflow.token = workflow.token
        confirm_workflow.restore()
        list(confirm_workflow)
        # Bart is now unsubscribed.
        member = self._mlist.regular_members.get_member(
            'anne.person@example.com')
        self.assertIsNone(member)
        # No further token is needed.
        self.assertIsNone(confirm_workflow.token)
        self.assertEqual(confirm_workflow.token_owner, TokenOwner.no_one)

    def test_do_confirmation_nonmember(self):
        # Attempt to confirm the unsubscription of a member who has already
        # been unsubscribed.
        self._mlist.unsubscription_policy = SubscriptionPolicy.confirm
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        list(workflow)
        # Anne is a member.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNotNone(member)
        self.assertEqual(member, workflow.member)
        # The token is owned by the subscriber.
        self.assertIsNotNone(workflow.token)
        self.assertEqual(workflow.token_owner, TokenOwner.subscriber)
        # Unsubscribe Anne out of band.
        member.unsubscribe()
        # Confirm.
        confirm_workflow = UnSubscriptionWorkflow(self._mlist)
        confirm_workflow.token = workflow.token
        confirm_workflow.restore()
        list(confirm_workflow)
        # No further token is needed.
        self.assertIsNone(confirm_workflow.token)
        self.assertEqual(confirm_workflow.token_owner, TokenOwner.no_one)

    def test_do_confirmation_nonmember_final_step(self):
        # Attempt to confirm the unsubscription of a member who has already
        # been unsubscribed.
        self._mlist.unsubscription_policy = SubscriptionPolicy.confirm
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        list(workflow)
        # Anne is a member.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNotNone(member)
        self.assertEqual(member, workflow.member)
        # The token is owned by the subscriber.
        self.assertIsNotNone(workflow.token)
        self.assertEqual(workflow.token_owner, TokenOwner.subscriber)
        # Confirm.
        confirm_workflow = UnSubscriptionWorkflow(self._mlist)
        confirm_workflow.token = workflow.token
        confirm_workflow.restore()
        confirm_workflow.run_until('do_unsubscription')
        self.assertEqual(member, confirm_workflow.member)
        # Unsubscribe Anne out of band.
        member.unsubscribe()
        list(confirm_workflow)
        self.assertIsNone(confirm_workflow.member)
        # No further token is needed.
        self.assertIsNone(confirm_workflow.token)
        self.assertEqual(confirm_workflow.token_owner, TokenOwner.no_one)

    def test_prevent_confirmation_replay_attacks(self):
        # Ensure that if the workflow requires two confirmations, e.g. first
        # the user confirming their subscription, and then the moderator
        # approving it, that different tokens are used in these two cases.
        self._mlist.unsubscription_policy = (
            SubscriptionPolicy.confirm_then_moderate)
        workflow = UnSubscriptionWorkflow(self._mlist, self.anne)
        # Run the state machine up to the first confirmation, and cache the
        # confirmation token.
        list(workflow)
        token = workflow.token
        # Anne is still a member of the mailing list.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNotNone(member)
        self.assertIsNotNone(workflow.member)
        # The token is owned by the subscriber.
        self.assertIsNotNone(workflow.token)
        self.assertEqual(workflow.token_owner, TokenOwner.subscriber)
        # The old token will not work for moderator approval.
        moderator_workflow = UnSubscriptionWorkflow(self._mlist)
        moderator_workflow.token = token
        moderator_workflow.restore()
        list(moderator_workflow)
        # The token is owned by the moderator.
        self.assertIsNotNone(moderator_workflow.token)
        self.assertEqual(moderator_workflow.token_owner, TokenOwner.moderator)
        # While we wait for the moderator to approve the subscription, note
        # that there's a new token for the next steps.
        self.assertNotEqual(token, moderator_workflow.token)
        # The old token won't work.
        final_workflow = UnSubscriptionWorkflow(self._mlist)
        final_workflow.token = token
        self.assertRaises(LookupError, final_workflow.restore)
        # Running this workflow will fail.
        self.assertRaises(AssertionError, list, final_workflow)
        # Anne is still not unsubscribed.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNotNone(member)
        self.assertIsNone(final_workflow.member)
        # However, if we use the new token, her unsubscription request will be
        # approved by the moderator.
        final_workflow.token = moderator_workflow.token
        final_workflow.restore()
        list(final_workflow)
        # And now Anne is unsubscribed.
        member = self._mlist.regular_members.get_member(self._anne)
        self.assertIsNone(member)
        # No further token is needed.
        self.assertIsNone(final_workflow.token)
        self.assertEqual(final_workflow.token_owner, TokenOwner.no_one)

    def test_confirmation_needed_and_pre_confirmed(self):
        # The subscription policy is 'confirm' but the subscription is
        # pre-confirmed so the moderation checks can be skipped.
        self._mlist.unsubscription_policy = SubscriptionPolicy.confirm
        workflow = UnSubscriptionWorkflow(
            self._mlist, self.anne, pre_confirmed=True, pre_approved=True)
        list(workflow)
        # Anne was unsubscribed.
        self.assertIsNone(workflow.token)
        self.assertEqual(workflow.token_owner, TokenOwner.no_one)
        self.assertIsNone(workflow.member)

    def test_confirmation_needed_moderator_address(self):
        address = self.anne.register('anne.person@example.com')
        self._mlist.subscribe(address)
        self._mlist.unsubscription_policy = SubscriptionPolicy.moderate
        workflow = UnSubscriptionWorkflow(self._mlist, address)
        # Get moderator approval.
        list(workflow)
        approved_workflow = UnSubscriptionWorkflow(self._mlist)
        approved_workflow.token = workflow.token
        approved_workflow.restore()
        list(approved_workflow)
        self.assertEqual(approved_workflow.subscriber, address)
        # Anne was unsubscribed.
        self.assertIsNone(approved_workflow.token)
        self.assertEqual(approved_workflow.token_owner, TokenOwner.no_one)
        self.assertIsNone(approved_workflow.member)
        member = self._mlist.regular_members.get_member(
            'anne.person@example.com')
        self.assertIsNone(member)
