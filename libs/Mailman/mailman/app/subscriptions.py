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

"""Handle subscriptions."""

import uuid
import logging

from datetime import timedelta
from email.utils import formataddr
from enum import Enum
from mailman.app.membership import delete_member
from mailman.app.workflow import Workflow
from mailman.core.i18n import _
from mailman.database.transaction import flush
from mailman.email.message import UserNotification
from mailman.interfaces.address import IAddress
from mailman.interfaces.bans import IBanManager
from mailman.interfaces.listmanager import ListDeletingEvent
from mailman.interfaces.mailinglist import SubscriptionPolicy
from mailman.interfaces.member import (
    AlreadySubscribedError, MemberRole, MembershipIsBannedError,
    NotAMemberError)
from mailman.interfaces.pending import IPendable, IPendings
from mailman.interfaces.subscriptions import (
    ISubscriptionManager, ISubscriptionService,
    SubscriptionConfirmationNeededEvent, SubscriptionPendingError, TokenOwner,
    UnsubscriptionConfirmationNeededEvent)
from mailman.interfaces.template import ITemplateLoader
from mailman.interfaces.user import IUser
from mailman.interfaces.usermanager import IUserManager
from mailman.interfaces.workflow import IWorkflowStateManager
from mailman.utilities.datetime import now
from mailman.utilities.string import expand, wrap
from public import public
from zope.component import getUtility
from zope.event import notify
from zope.interface import implementer


log = logging.getLogger('mailman.subscribe')


class WhichSubscriber(Enum):
    address = 1
    user = 2


@implementer(IPendable)
class PendableSubscription(dict):
    PEND_TYPE = 'subscription'


@implementer(IPendable)
class PendableUnsubscription(dict):
    PEND_TYPE = 'unsubscription'


class _SubscriptionWorkflowCommon(Workflow):
    """Common support between subscription and unsubscription."""

    PENDABLE_CLASS = None

    def __init__(self, mlist, subscriber):
        super().__init__()
        self.mlist = mlist
        self.address = None
        self.user = None
        self.which = None
        self.member = None
        self._set_token(TokenOwner.no_one)
        # The subscriber must be either an IUser or IAddress.
        if IAddress.providedBy(subscriber):
            self.address = subscriber
            self.user = self.address.user
            self.which = WhichSubscriber.address
        elif IUser.providedBy(subscriber):
            self.address = subscriber.preferred_address
            self.user = subscriber
            self.which = WhichSubscriber.user
        self.subscriber = subscriber

    @property
    def user_key(self):
        # For save.
        return self.user.user_id.hex

    @user_key.setter
    def user_key(self, hex_key):
        # For restore.
        uid = uuid.UUID(hex_key)
        self.user = getUtility(IUserManager).get_user_by_id(uid)
        if self.user is None:
            self.user = self.address.user

    @property
    def address_key(self):
        # For save.
        return self.address.email

    @address_key.setter
    def address_key(self, email):
        # For restore.
        self.address = getUtility(IUserManager).get_address(email)
        assert self.address is not None

    @property
    def subscriber_key(self):
        return self.which.value

    @subscriber_key.setter
    def subscriber_key(self, key):
        self.which = WhichSubscriber(key)

    @property
    def token_owner_key(self):
        return self.token_owner.value

    @token_owner_key.setter
    def token_owner_key(self, value):
        self.token_owner = TokenOwner(value)

    def _set_token(self, token_owner):
        assert isinstance(token_owner, TokenOwner)
        pendings = getUtility(IPendings)
        # Clear out the previous pending token if there is one.
        if self.token is not None:
            pendings.confirm(self.token)
        # Create a new token to prevent replay attacks.  It seems like this
        # would produce the same token, but it won't because the pending adds a
        # bit of randomization.
        self.token_owner = token_owner
        if token_owner is TokenOwner.no_one:
            self.token = None
            return
        pendable = self.PENDABLE_CLASS(
            list_id=self.mlist.list_id,
            email=self.address.email,
            display_name=self.address.display_name,
            when=now().replace(microsecond=0).isoformat(),
            token_owner=token_owner.name,
            )
        self.token = pendings.add(pendable, timedelta(days=3650))


@public
class SubscriptionWorkflow(_SubscriptionWorkflowCommon):
    """Workflow of a subscription request."""

    PENDABLE_CLASS = PendableSubscription
    INITIAL_STATE = 'sanity_checks'
    SAVE_ATTRIBUTES = (
        'pre_approved',
        'pre_confirmed',
        'pre_verified',
        'address_key',
        'subscriber_key',
        'user_key',
        'token_owner_key',
        )

    def __init__(self, mlist, subscriber=None, *,
                 pre_verified=False, pre_confirmed=False, pre_approved=False):
        super().__init__(mlist, subscriber)
        self.pre_verified = pre_verified
        self.pre_confirmed = pre_confirmed
        self.pre_approved = pre_approved

    def _step_sanity_checks(self):
        # Ensure that we have both an address and a user, even if the address
        # is not verified.  We can't set the preferred address until it is
        # verified.
        if self.user is None:
            # The address has no linked user so create one, link it, and set
            # the user's preferred address.
            assert self.address is not None, 'No address or user'
            self.user = getUtility(IUserManager).make_user(self.address.email)
        if self.address is None:
            assert self.user.preferred_address is None, (
                "Preferred address exists, but wasn't used in constructor")
            addresses = list(self.user.addresses)
            if len(addresses) == 0:
                raise AssertionError('User has no addresses: {}'.format(
                    self.user))
            # This is rather arbitrary, but we have no choice.
            self.address = addresses[0]
        assert self.user is not None and self.address is not None, (
            'Insane sanity check results')
        # Is this subscriber already a member?
        if (self.which is WhichSubscriber.user and
                self.user.preferred_address is not None):
            subscriber = self.user
        else:
            subscriber = self.address
        if self.mlist.is_subscribed(subscriber):
            # 2017-04-22 BAW: This branch actually *does* get covered, as I've
            # verified by a full coverage run, but diffcov for some reason
            # claims that the test added in the branch that added this code
            # does not cover the change.  That seems like a bug in diffcov.
            raise AlreadySubscribedError(           # pragma: no cover
                self.mlist.fqdn_listname,
                self.address.email,
                MemberRole.member)
        # Is this email address banned?
        if IBanManager(self.mlist).is_banned(self.address.email):
            raise MembershipIsBannedError(self.mlist, self.address.email)
        # Check if there is already a subscription request for this email.
        pendings = getUtility(IPendings).find(
            mlist=self.mlist,
            pend_type='subscription')
        for token, pendable in pendings:
            if pendable['email'] == self.address.email:
                raise SubscriptionPendingError(self.mlist, self.address.email)
        # Start out with the subscriber being the token owner.
        self.push('verification_checks')

    def _step_verification_checks(self):
        # Is the address already verified, or is the pre-verified flag set?
        if self.address.verified_on is None:
            if self.pre_verified:
                self.address.verified_on = now()
            else:
                # The address being subscribed is not yet verified, so we need
                # to send a validation email that will also confirm that the
                # user wants to be subscribed to this mailing list.
                self.push('send_confirmation')
                return
        self.push('confirmation_checks')

    def _step_confirmation_checks(self):
        # If the list's subscription policy is open, then the user can be
        # subscribed right here and now.
        if self.mlist.subscription_policy is SubscriptionPolicy.open:
            self.push('do_subscription')
            return
        # If we do not need the user's confirmation, then skip to the
        # moderation checks.
        if self.mlist.subscription_policy is SubscriptionPolicy.moderate:
            self.push('moderation_checks')
            return
        # If the subscription has been pre-confirmed, then we can skip the
        # confirmation check can be skipped.  If moderator approval is
        # required we need to check that, otherwise we can go straight to
        # subscription.
        if self.pre_confirmed:
            next_step = (
                'moderation_checks'
                if self.mlist.subscription_policy is
                    SubscriptionPolicy.confirm_then_moderate   # noqa: E131
                else 'do_subscription')
            self.push(next_step)
            return
        # The user must confirm their subscription.
        self.push('send_confirmation')

    def _step_moderation_checks(self):
        # Does the moderator need to approve the subscription request?
        assert self.mlist.subscription_policy in (
            SubscriptionPolicy.moderate,
            SubscriptionPolicy.confirm_then_moderate,
            ), self.mlist.subscription_policy
        if self.pre_approved:
            self.push('do_subscription')
        else:
            self.push('get_moderator_approval')

    def _step_get_moderator_approval(self):
        # Here's the next step in the workflow, assuming the moderator
        # approves of the subscription.  If they don't, the workflow and
        # subscription request will just be thrown away.
        self._set_token(TokenOwner.moderator)
        self.push('subscribe_from_restored')
        self.save()
        log.info('{}: held subscription request from {}'.format(
            self.mlist.fqdn_listname, self.address.email))
        # Possibly send a notification to the list moderators.
        if self.mlist.admin_immed_notify:
            subject = _(
                'New subscription request to $self.mlist.display_name '
                'from $self.address.email')
            username = formataddr(
                (self.subscriber.display_name, self.address.email))
            template = getUtility(ITemplateLoader).get(
                'list:admin:action:subscribe', self.mlist)
            text = wrap(expand(template, self.mlist, dict(
                member=username,
                )))
            # This message should appear to come from the <list>-owner so as
            # to avoid any useless bounce processing.
            msg = UserNotification(
                self.mlist.owner_address, self.mlist.owner_address,
                subject, text, self.mlist.preferred_language)
            msg.send(self.mlist)
        # The workflow must stop running here.
        raise StopIteration

    def _step_subscribe_from_restored(self):
        # Prevent replay attacks.
        self._set_token(TokenOwner.no_one)
        # Restore a little extra state that can't be stored in the database
        # (because the order of setattr() on restore is indeterminate), then
        # subscribe the user.
        if self.which is WhichSubscriber.address:
            self.subscriber = self.address
        else:
            assert self.which is WhichSubscriber.user
            self.subscriber = self.user
        self.push('do_subscription')

    def _step_do_subscription(self):
        # We can immediately subscribe the user to the mailing list.
        self.member = self.mlist.subscribe(self.subscriber)
        assert self.token is None and self.token_owner is TokenOwner.no_one, (
            'Unexpected active token at end of subscription workflow')

    def _step_send_confirmation(self):
        self._set_token(TokenOwner.subscriber)
        self.push('do_confirm_verify')
        self.save()
        # Triggering this event causes the confirmation message to be sent.
        notify(SubscriptionConfirmationNeededEvent(
            self.mlist, self.token, self.address.email))
        # Now we wait for the confirmation.
        raise StopIteration

    def _step_do_confirm_verify(self):
        # Restore a little extra state that can't be stored in the database
        # (because the order of setattr() on restore is indeterminate), then
        # continue with the confirmation/verification step.
        if self.which is WhichSubscriber.address:
            self.subscriber = self.address
        else:
            assert self.which is WhichSubscriber.user
            self.subscriber = self.user
        # Reset the token so it can't be used in a replay attack.
        self._set_token(TokenOwner.no_one)
        # The user has confirmed their subscription request, and also verified
        # their email address if necessary.  This latter needs to be set on the
        # IAddress, but there's nothing more to do about the confirmation step.
        # We just continue along with the workflow.
        if self.address.verified_on is None:
            self.address.verified_on = now()
        # The next step depends on the mailing list's subscription policy.
        next_step = ('moderation_checks'
                     if self.mlist.subscription_policy in (
                         SubscriptionPolicy.moderate,
                         SubscriptionPolicy.confirm_then_moderate,
                         )
                     else 'do_subscription')
        self.push(next_step)


@public
class UnSubscriptionWorkflow(_SubscriptionWorkflowCommon):
    """Workflow of a unsubscription request."""

    PENDABLE_CLASS = PendableUnsubscription
    INITIAL_STATE = 'subscription_checks'
    SAVE_ATTRIBUTES = (
        'pre_approved',
        'pre_confirmed',
        'address_key',
        'user_key',
        'subscriber_key',
        'token_owner_key',
        )

    def __init__(self, mlist, subscriber=None, *,
                 pre_approved=False, pre_confirmed=False):
        super().__init__(mlist, subscriber)
        if IAddress.providedBy(subscriber) or IUser.providedBy(subscriber):
            self.member = self.mlist.regular_members.get_member(
                self.address.email)
        self.pre_confirmed = pre_confirmed
        self.pre_approved = pre_approved

    def _step_subscription_checks(self):
        assert self.mlist.is_subscribed(self.subscriber)
        self.push('confirmation_checks')

    def _step_confirmation_checks(self):
        # If list's unsubscription policy is open, the user can unsubscribe
        # right now.
        if self.mlist.unsubscription_policy is SubscriptionPolicy.open:
            self.push('do_unsubscription')
            return
        # If we don't need the user's confirmation, then skip to the moderation
        # checks.
        if self.mlist.unsubscription_policy is SubscriptionPolicy.moderate:
            self.push('moderation_checks')
            return
        # If the request is pre-confirmed, then the user can unsubscribe right
        # now.
        if self.pre_confirmed:
            self.push('do_unsubscription')
            return
        # The user must confirm their un-subsbcription.
        self.push('send_confirmation')

    def _step_send_confirmation(self):
        self._set_token(TokenOwner.subscriber)
        self.push('do_confirm_verify')
        self.save()
        notify(UnsubscriptionConfirmationNeededEvent(
            self.mlist, self.token, self.address.email))
        raise StopIteration

    def _step_moderation_checks(self):
        # Does the moderator need to approve the unsubscription request?
        assert self.mlist.unsubscription_policy in (
            SubscriptionPolicy.moderate,
            SubscriptionPolicy.confirm_then_moderate,
            ), self.mlist.unsubscription_policy
        if self.pre_approved:
            self.push('do_unsubscription')
        else:
            self.push('get_moderator_approval')

    def _step_get_moderator_approval(self):
        self._set_token(TokenOwner.moderator)
        self.push('unsubscribe_from_restored')
        self.save()
        log.info('{}: held unsubscription request from {}'.format(
            self.mlist.fqdn_listname, self.address.email))
        if self.mlist.admin_immed_notify:
            subject = _(
                'New unsubscription request to $self.mlist.display_name '
                'from $self.address.email')
            username = formataddr(
                (self.subscriber.display_name, self.address.email))
            template = getUtility(ITemplateLoader).get(
                'list:admin:action:unsubscribe', self.mlist)
            text = wrap(expand(template, self.mlist, dict(
                member=username,
                )))
            # This message should appear to come from the <list>-owner so as
            # to avoid any useless bounce processing.
            msg = UserNotification(
                self.mlist.owner_address, self.mlist.owner_address,
                subject, text, self.mlist.preferred_language)
            msg.send(self.mlist)
        # The workflow must stop running here
        raise StopIteration

    def _step_do_confirm_verify(self):
        # Restore a little extra state that can't be stored in the database
        # (because the order of setattr() on restore is indeterminate), then
        # continue with the confirmation/verification step.
        if self.which is WhichSubscriber.address:
            self.subscriber = self.address
        else:
            assert self.which is WhichSubscriber.user
            self.subscriber = self.user
        # Reset the token so it can't be used in a replay attack.
        self._set_token(TokenOwner.no_one)
        # Restore the member object.
        self.member = self.mlist.regular_members.get_member(self.address.email)
        # It's possible the member was already unsubscribed while we were
        # waiting for the confirmation.
        if self.member is None:
            return
        # The user has confirmed their unsubscription request
        next_step = ('moderation_checks'
                     if self.mlist.unsubscription_policy in (
                          SubscriptionPolicy.moderate,
                          SubscriptionPolicy.confirm_then_moderate,
                          )
                     else 'do_unsubscription')
        self.push(next_step)

    def _step_do_unsubscription(self):
        try:
            delete_member(self.mlist, self.address.email)
        except NotAMemberError:
            # The member has already been unsubscribed.
            pass
        self.member = None
        assert self.token is None and self.token_owner is TokenOwner.no_one, (
            'Unexpected active token at end of subscription workflow')

    def _step_unsubscribe_from_restored(self):
        # Prevent replay attacks.
        self._set_token(TokenOwner.no_one)
        if self.which is WhichSubscriber.address:
            self.subscriber = self.address
        else:
            assert self.which is WhichSubscriber.user
            self.subscriber = self.user
        self.push('do_unsubscription')


@public
@implementer(ISubscriptionManager)
class SubscriptionManager:
    def __init__(self, mlist):
        self._mlist = mlist

    def register(self, subscriber=None, *,
                 pre_verified=False, pre_confirmed=False, pre_approved=False):
        """See `ISubscriptionManager`."""
        workflow = SubscriptionWorkflow(
            self._mlist, subscriber,
            pre_verified=pre_verified,
            pre_confirmed=pre_confirmed,
            pre_approved=pre_approved)
        list(workflow)
        return workflow.token, workflow.token_owner, workflow.member

    def unregister(self, subscriber=None, *,
                   pre_confirmed=False, pre_approved=False):
        workflow = UnSubscriptionWorkflow(
            self._mlist, subscriber,
            pre_confirmed=pre_confirmed,
            pre_approved=pre_approved)
        list(workflow)
        return workflow.token, workflow.token_owner, workflow.member

    def confirm(self, token):
        if token is None:
            raise LookupError
        pendable = getUtility(IPendings).confirm(token, expunge=False)
        if pendable is None:
            raise LookupError
        workflow_type = pendable.get('type')
        assert workflow_type in (PendableSubscription.PEND_TYPE,
                                 PendableUnsubscription.PEND_TYPE)
        workflow = (SubscriptionWorkflow
                    if workflow_type == PendableSubscription.PEND_TYPE
                    else UnSubscriptionWorkflow)(self._mlist)
        workflow.token = token
        workflow.restore()
        # In order to just run the whole workflow, all we need to do
        # is iterate over the workflow object. On calling the __next__
        # over the workflow iterator it automatically executes the steps
        # that needs to be done.
        list(workflow)
        return workflow.token, workflow.token_owner, workflow.member

    def discard(self, token):
        with flush():
            getUtility(IPendings).confirm(token)
            getUtility(IWorkflowStateManager).discard(token)


def _handle_confirmation_needed_events(event, template_name):
    subject = 'confirm {}'.format(event.token)
    confirm_address = event.mlist.confirm_address(event.token)
    email_address = event.email
    # Send a verification email to the address.
    template = getUtility(ITemplateLoader).get(template_name, event.mlist)
    text = expand(template, event.mlist, dict(
        token=event.token,
        subject=subject,
        confirm_email=confirm_address,
        user_email=email_address,
        # For backward compatibility.
        confirm_address=confirm_address,
        email_address=email_address,
        domain_name=event.mlist.domain.mail_host,
        contact_address=event.mlist.owner_address,
        ))
    msg = UserNotification(email_address, confirm_address, subject, text)
    msg.send(event.mlist, add_precedence=False)


@public
def handle_SubscriptionConfirmationNeededEvent(event):
    if not isinstance(event, SubscriptionConfirmationNeededEvent):
        return
    _handle_confirmation_needed_events(event, 'list:user:action:subscribe')


@public
def handle_UnsubscriptionConfirmationNeededEvent(event):
    if not isinstance(event, UnsubscriptionConfirmationNeededEvent):
        return
    _handle_confirmation_needed_events(event, 'list:user:action:unsubscribe')


@public
def handle_ListDeletingEvent(event):
    """Delete a mailing list's members when the list is being deleted."""

    if not isinstance(event, ListDeletingEvent):
        return
    # Find all the members still associated with the mailing list.
    members = getUtility(ISubscriptionService).find_members(
        list_id=event.mailing_list.list_id)
    for member in members:
        member.unsubscribe()
