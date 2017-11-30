# Copyright (C) 2010-2017 by the Free Software Foundation, Inc.
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

"""REST for members."""

from lazr.config import as_boolean
from mailman.app.membership import add_member, delete_member
from mailman.interfaces.action import Action
from mailman.interfaces.address import IAddress
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.member import (
    AlreadySubscribedError, DeliveryMode, MemberRole, MembershipError,
    MembershipIsBannedError, MissingPreferredAddressError)
from mailman.interfaces.subscriptions import (
    ISubscriptionManager, ISubscriptionService, RequestRecord,
    SubscriptionPendingError, TokenOwner)
from mailman.interfaces.user import IUser, UnverifiedAddressError
from mailman.interfaces.usermanager import IUserManager
from mailman.rest.helpers import (
    CollectionMixin, NotFound, accepted, bad_request, child, conflict,
    created, etag, no_content, not_found, okay)
from mailman.rest.preferences import Preferences, ReadOnlyPreferences
from mailman.rest.validator import (
    Validator, enum_validator, subscriber_validator)
from public import public
from uuid import UUID
from zope.component import getUtility


class _MemberBase(CollectionMixin):
    """Shared base class for member representations."""

    def _resource_as_dict(self, member):
        """See `CollectionMixin`."""
        enum, dot, role = str(member.role).partition('.')
        # The member will always have a member id and an address id.  It will
        # only have a user id if the address is linked to a user.
        # E.g. nonmembers we've only seen via postings to lists they are not
        # subscribed to will not have a user id.  The user_id and the
        # member_id are UUIDs.  In API 3.0 we use the integer equivalent of
        # the UID in the URL, but in API 3.1 we use the hex equivalent.  See
        # issue #121 for details.
        member_id = self.api.from_uuid(member.member_id)
        response = dict(
            address=self.api.path_to(
                'addresses/{}'.format(member.address.email)),
            delivery_mode=member.delivery_mode,
            email=member.address.email,
            list_id=member.list_id,
            member_id=member_id,
            role=role,
            self_link=self.api.path_to('members/{}'.format(member_id)),
            )
        # Add the moderation action if overriding the list's default.
        if member.moderation_action is not None:
            response['moderation_action'] = member.moderation_action
        # Add the user link if there is one.
        user = member.user
        if user is not None:
            user_id = self.api.from_uuid(user.user_id)
            response['user'] = self.api.path_to('users/{}'.format(user_id))
        return response

    def _get_collection(self, request):
        """See `CollectionMixin`."""
        return list(getUtility(ISubscriptionService))


@public
class MemberCollection(_MemberBase):
    """Abstract class for supporting submemberships.

    This is used for example to return a resource representing all the
    memberships of a mailing list, or all memberships for a specific email
    address.
    """
    def _get_collection(self, request):
        """See `CollectionMixin`."""
        raise NotImplementedError

    def on_get(self, request, response):
        """roster/[members|owners|moderators]"""
        resource = self._make_collection(request)
        okay(response, etag(resource))


@public
class AMember(_MemberBase):
    """A member."""

    def __init__(self, member_id):
        # The member_id is either the member's UUID or the string
        # representation of the member's UUID.
        service = getUtility(ISubscriptionService)
        self._member_id = member_id
        self._member = (None if member_id is None
                        else service.get_member(member_id))

    def on_get(self, request, response):
        """Return a single member end-point."""
        if self._member is None:
            not_found(response)
        else:
            okay(response, self._resource_as_json(self._member))

    @child()
    def preferences(self, context, segments):
        """/members/<id>/preferences"""
        if len(segments) != 0:
            return NotFound(), []
        if self._member is None:
            return NotFound(), []
        member_id = self.api.from_uuid(self._member_id)
        child = Preferences(
            self._member.preferences, 'members/{}'.format(member_id))
        return child, []

    @child()
    def all(self, context, segments):
        """/members/<id>/all/preferences"""
        if len(segments) == 0:
            return NotFound(), []
        if self._member is None:
            return NotFound(), []
        member_id = self.api.from_uuid(self._member_id)
        child = ReadOnlyPreferences(
            self._member, 'members/{}/all'.format(member_id))
        return child, []

    def on_delete(self, request, response):
        """Delete the member (i.e. unsubscribe)."""
        # Leaving a list is a bit different than deleting a moderator or
        # owner.  Handle the former case first.  For now too, we will not send
        # an admin or user notification.
        if self._member is None:
            not_found(response)
            return
        mlist = getUtility(IListManager).get_by_list_id(self._member.list_id)
        if self._member.role is MemberRole.member:
            delete_member(mlist, self._member.address.email, False, False)
        else:
            self._member.unsubscribe()
        no_content(response)

    def on_patch(self, request, response):
        """Patch the membership.

        This is how subscription changes are done.
        """
        if self._member is None:
            not_found(response)
            return
        try:
            values = Validator(
                address=str,
                delivery_mode=enum_validator(DeliveryMode),
                moderation_action=enum_validator(Action, allow_blank=True),
                _optional=('address', 'delivery_mode', 'moderation_action'),
                )(request)
        except ValueError as error:
            bad_request(response, str(error))
            return
        if 'address' in values:
            email = values['address']
            address = getUtility(IUserManager).get_address(email)
            if address is None:
                bad_request(response, b'Address not registered')
                return
            try:
                self._member.address = address
            except (MembershipError, UnverifiedAddressError) as error:
                bad_request(response, str(error))
                return
        if 'delivery_mode' in values:
            self._member.preferences.delivery_mode = values['delivery_mode']
        if 'moderation_action' in values:
            self._member.moderation_action = values['moderation_action']
        no_content(response)


@public
class AllMembers(_MemberBase):
    """The members."""

    def on_post(self, request, response):
        """Create a new member."""
        try:
            validator = Validator(
                list_id=str,
                subscriber=subscriber_validator(self.api),
                display_name=str,
                delivery_mode=enum_validator(DeliveryMode),
                role=enum_validator(MemberRole),
                pre_verified=as_boolean,
                pre_confirmed=as_boolean,
                pre_approved=as_boolean,
                _optional=('delivery_mode', 'display_name', 'role',
                           'pre_verified', 'pre_confirmed', 'pre_approved'))
            arguments = validator(request)
        except ValueError as error:
            bad_request(response, str(error))
            return
        # Dig the mailing list out of the arguments.
        list_id = arguments.pop('list_id')
        mlist = getUtility(IListManager).get_by_list_id(list_id)
        if mlist is None:
            bad_request(response, b'No such list')
            return
        # Figure out what kind of subscriber is being registered.  Either it's
        # a user via their preferred email address or it's an explicit address.
        # If it's a UUID, then it must be associated with an existing user.
        subscriber = arguments.pop('subscriber')
        user_manager = getUtility(IUserManager)
        # We use the display name if there is one.
        display_name = arguments.pop('display_name', '')
        if isinstance(subscriber, UUID):
            user = user_manager.get_user_by_id(subscriber)
            if user is None:
                bad_request(response, b'No such user')
                return
            subscriber = user
        else:
            # This must be an email address.  See if there's an existing
            # address object associated with this email.
            address = user_manager.get_address(subscriber)
            if address is None:
                # Create a new address, which of course will not be validated.
                address = user_manager.create_address(
                    subscriber, display_name)
            subscriber = address
        # What role are we subscribing?  Regular members go through the
        # subscription policy workflow while owners, moderators, and
        # nonmembers go through the legacy API for now.
        role = arguments.pop('role', MemberRole.member)
        if role is MemberRole.member:
            # Get the pre_ flags for the subscription workflow.
            pre_verified = arguments.pop('pre_verified', False)
            pre_confirmed = arguments.pop('pre_confirmed', False)
            pre_approved = arguments.pop('pre_approved', False)
            # Now we can run the registration process until either the
            # subscriber is subscribed, or the workflow is paused for
            # verification, confirmation, or approval.
            registrar = ISubscriptionManager(mlist)
            try:
                token, token_owner, member = registrar.register(
                    subscriber,
                    pre_verified=pre_verified,
                    pre_confirmed=pre_confirmed,
                    pre_approved=pre_approved)
            except AlreadySubscribedError:
                conflict(response, b'Member already subscribed')
                return
            except MissingPreferredAddressError:
                bad_request(response, b'User has no preferred address')
                return
            except MembershipIsBannedError:
                bad_request(response, b'Membership is banned')
                return
            except SubscriptionPendingError:
                conflict(response, b'Subscription request already pending')
                return
            if token is None:
                assert token_owner is TokenOwner.no_one, token_owner
                # The subscription completed.  Let's get the resulting member
                # and return the location to the new member.  Member ids are
                # UUIDs and need to be converted to URLs because JSON doesn't
                # directly support UUIDs.
                member_id = self.api.from_uuid(member.member_id)
                location = self.api.path_to('members/{}'.format(member_id))
                created(response, location)
                return
            # The member could not be directly subscribed because there are
            # some out-of-band steps that need to be completed.  E.g. the user
            # must confirm their subscription or the moderator must approve
            # it.  In this case, an HTTP 202 Accepted is exactly the code that
            # we should use, and we'll return both the confirmation token and
            # the "token owner" so the client knows who should confirm it.
            assert token is not None, token
            assert token_owner is not TokenOwner.no_one, token_owner
            assert member is None, member
            content = dict(token=token, token_owner=token_owner.name)
            accepted(response, etag(content))
            return
        # 2015-04-15 BAW: We're subscribing some role other than a regular
        # member.  Use the legacy API for this for now.
        assert role in (MemberRole.owner,
                        MemberRole.moderator,
                        MemberRole.nonmember)
        # 2015-04-15 BAW: We're limited to using an email address with this
        # legacy API, so if the subscriber is a user, the user must have a
        # preferred address, which we'll use, even though it will subscribe
        # the explicit address.  It is an error if the user does not have a
        # preferred address.
        #
        # If the subscriber is an address object, just use that.
        if IUser.providedBy(subscriber):
            if subscriber.preferred_address is None:
                bad_request(response, b'User without preferred address')
                return
            email = subscriber.preferred_address.email
        else:
            assert IAddress.providedBy(subscriber)
            email = subscriber.email
        delivery_mode = arguments.pop('delivery_mode', DeliveryMode.regular)
        record = RequestRecord(email, display_name, delivery_mode)
        try:
            member = add_member(mlist, record, role)
        except MembershipIsBannedError:
            bad_request(response, b'Membership is banned')
            return
        except AlreadySubscribedError:
            bad_request(response,
                        '{} is already an {} of {}'.format(
                            email, role.name, mlist.fqdn_listname))
            return
        # The subscription completed.  Let's get the resulting member
        # and return the location to the new member.  Member ids are
        # UUIDs and need to be converted to URLs because JSON doesn't
        # directly support UUIDs.
        member_id = self.api.from_uuid(member.member_id)
        location = self.api.path_to('members/{}'.format(member_id))
        created(response, location)

    def on_get(self, request, response):
        """/members"""
        resource = self._make_collection(request)
        okay(response, etag(resource))


class _FoundMembers(MemberCollection):
    """The found members collection."""

    def __init__(self, members, api):
        super().__init__()
        self._members = members
        self.api = api

    def _get_collection(self, request):
        """See `CollectionMixin`."""
        return self._members


@public
class FindMembers(_MemberBase):
    """/members/find"""

    def on_get(self, request, response):
        return self._find(request, response)

    def on_post(self, request, response):
        return self._find(request, response)

    def _find(self, request, response):
        """Find a member"""
        service = getUtility(ISubscriptionService)
        validator = Validator(
            list_id=str,
            subscriber=str,
            role=enum_validator(MemberRole),
            # Allow pagination.
            page=int,
            count=int,
            _optional=('list_id', 'subscriber', 'role', 'page', 'count'))
        try:
            data = validator(request)
        except ValueError as error:
            bad_request(response, str(error))
        else:
            # Remove any optional pagination query elements; they will be
            # handled later.
            data.pop('page', None)
            data.pop('count', None)
            members = service.find_members(**data)
            resource = _FoundMembers(members, self.api)
            okay(response, etag(resource._make_collection(request)))
