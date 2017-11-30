# Copyright (C) 2007-2017 by the Free Software Foundation, Inc.
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

"""Application support for membership management."""

from email.utils import formataddr
from mailman.app.notifications import (
    send_admin_subscription_notice, send_goodbye_message,
    send_welcome_message)
from mailman.core.i18n import _
from mailman.email.message import OwnerNotification
from mailman.interfaces.address import IAddress
from mailman.interfaces.bans import IBanManager
from mailman.interfaces.member import (
    AlreadySubscribedError, MemberRole, MembershipIsBannedError,
    NotAMemberError, SubscriptionEvent)
from mailman.interfaces.template import ITemplateLoader
from mailman.interfaces.user import IUser
from mailman.interfaces.usermanager import IUserManager
from mailman.utilities.string import expand
from public import public
from zope.component import getUtility


@public
def add_member(mlist, record, role=MemberRole.member):
    """Add a member right now.

    The member's subscription must be approved by whatever policy the list
    enforces.

    :param mlist: The mailing list to add the member to.
    :type mlist: `IMailingList`
    :param record: a subscription request record.
    :type record: RequestRecord
    :param role: The membership role for this subscription.
    :type role: `MemberRole`
    :return: The just created member.
    :rtype: `IMember`
    :raises AlreadySubscribedError: if the user is already subscribed to
        the mailing list.
    :raises InvalidEmailAddressError: if the email address is not valid.
    :raises MembershipIsBannedError: if the membership is not allowed.
    """
    # Check to see if the email address is banned.
    if IBanManager(mlist).is_banned(record.email):
        raise MembershipIsBannedError(mlist, record.email)
    # Make sure there is a user linked with the given address.
    user_manager = getUtility(IUserManager)
    user = user_manager.make_user(record.email, record.display_name)
    user.preferences.preferred_language = record.language
    # Subscribe the address, not the user.
    # We're looking for two versions of the email address, the case
    # preserved version and the case insensitive version.   We'll
    # subscribe the version with matching case if it exists, otherwise
    # we'll use one of the matching case-insensitively ones.  It's
    # undefined which one we pick.
    case_preserved = None
    case_insensitive = None
    for address in user.addresses:
        if address.original_email == record.email:
            case_preserved = address
        if address.email == record.email.lower():   # pragma: no branch
            case_insensitive = address
    assert case_preserved is not None or case_insensitive is not None, (
        'Could not find a linked address for: {}'.format(record.email))
    address = (case_preserved if case_preserved is not None
               else case_insensitive)
    # Create the member and set the appropriate preferences.  It's
    # possible we're subscribing the lower cased version of the address;
    # if that's already subscribed re-issue the exception with the correct
    # email address (i.e. the one passed in here).
    try:
        member = mlist.subscribe(address, role)
    except AlreadySubscribedError as error:
        raise AlreadySubscribedError(
            error.fqdn_listname, record.email, error.role)
    member.preferences.preferred_language = record.language
    member.preferences.delivery_mode = record.delivery_mode
    # Check for and remove nonmember subscriptions of the user to this list.
    if role is MemberRole.member:
        for address in user.addresses:
            nonmember = mlist.nonmembers.get_member(address.email)
            if nonmember is not None:
                nonmember.unsubscribe()
    return member


@public
def delete_member(mlist, email, admin_notif=None, userack=None):
    """Delete a member right now.

    :param mlist: The mailing list to remove the member from.
    :type mlist: `IMailingList`
    :param email: The email address to unsubscribe.
    :type email: string
    :param admin_notif: Whether the list administrator should be notified that
        this member was deleted.
    :type admin_notif: bool, or None to let the mailing list's
        `admin_notify_mchange` attribute decide.
    :raises NotAMemberError: if the address is not a member of the
        mailing list.
    """
    if userack is None:
        userack = mlist.send_goodbye_message
    if admin_notif is None:
        admin_notif = mlist.admin_notify_mchanges
    # Delete a member, for which we know the approval has been made.
    member = mlist.members.get_member(email)
    if member is None:
        raise NotAMemberError(mlist, email)
    language = member.preferred_language
    member.unsubscribe()
    # And send an acknowledgement to the user...
    if userack:
        send_goodbye_message(mlist, email, language)
    # ...and to the administrator.
    if admin_notif:
        user = getUtility(IUserManager).get_user(email)
        display_name = user.display_name
        subject = _('$mlist.display_name unsubscription notification')
        text = expand(getUtility(ITemplateLoader).get(
            'list:admin:notice:unsubscribe', mlist),
            mlist, dict(
                member=formataddr((display_name, email)),
                ))
        msg = OwnerNotification(mlist, subject, text,
                                roster=mlist.administrators)
        msg.send(mlist)


@public
def handle_SubscriptionEvent(event):
    if not isinstance(event, SubscriptionEvent):
        return
    member = event.member
    # Only send notifications if a member (as opposed to a moderator,
    # non-member, or owner) is being subscribed.
    if member.role is not MemberRole.member:
        return
    mlist = member.mailing_list
    # Maybe send the list administrators a notification.
    if mlist.admin_notify_mchanges:
        subscriber = member.subscriber
        if IAddress.providedBy(subscriber):
            address = subscriber.email
            display_name = subscriber.display_name
        else:
            assert IUser.providedBy(subscriber)
            address = subscriber.preferred_address.email
            display_name = subscriber.display_name
        send_admin_subscription_notice(mlist, address, display_name)
    # Maybe send a welcome message to the new member.
    if mlist.send_welcome_message:
        send_welcome_message(mlist, member, member.preferred_language)
