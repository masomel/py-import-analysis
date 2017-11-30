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

"""REST for mailing lists."""

from lazr.config import as_boolean
from mailman.app.digests import (
    bump_digest_number_and_volume, maybe_send_digest_now)
from mailman.app.lifecycle import (
    InvalidListNameError, create_list, remove_list)
from mailman.config import config
from mailman.interfaces.address import InvalidEmailAddressError
from mailman.interfaces.domain import BadDomainSpecificationError
from mailman.interfaces.listmanager import (
    IListManager, ListAlreadyExistsError)
from mailman.interfaces.mailinglist import IListArchiverSet
from mailman.interfaces.member import MemberRole
from mailman.interfaces.styles import IStyleManager
from mailman.interfaces.subscriptions import ISubscriptionService
from mailman.rest.bans import BannedEmails
from mailman.rest.header_matches import HeaderMatches
from mailman.rest.helpers import (
    BadRequest, CollectionMixin, GetterSetter, NotFound, accepted,
    bad_request, child, created, etag, no_content, not_found, okay)
from mailman.rest.listconf import ListConfiguration
from mailman.rest.members import AMember, MemberCollection
from mailman.rest.post_moderation import HeldMessages
from mailman.rest.sub_moderation import SubscriptionRequests
from mailman.rest.uris import AListURI, AllListURIs
from mailman.rest.validator import Validator, list_of_strings_validator
from public import public
from zope.component import getUtility


def member_matcher(segments):
    """A matcher of member URLs inside mailing lists.

    e.g. /<role>/aperson@example.org
    """
    if len(segments) != 2:
        return None
    try:
        role = MemberRole[segments[0]]
    except KeyError:
        # Not a valid role.
        return None
    return (), dict(role=role, email=segments[1]), ()


def roster_matcher(segments):
    """A matcher of all members URLs inside mailing lists.

    e.g. /roster/<role>
    """
    if len(segments) != 2 or segments[0] != 'roster':
        return None
    try:
        return (), dict(role=MemberRole[segments[1]]), ()
    except KeyError:
        # Not a valid role.
        return None


def config_matcher(segments):
    """A matcher for a mailing list's configuration resource.

    e.g. /config
    e.g. /config/description
    """
    if len(segments) < 1 or segments[0] != 'config':
        return None
    if len(segments) == 1:
        return (), {}, ()
    if len(segments) == 2:
        return (), dict(attribute=segments[1]), ()
    # More segments are not allowed.
    return None


class _ListBase(CollectionMixin):
    """Shared base class for mailing list representations."""

    def _resource_as_dict(self, mlist):
        """See `CollectionMixin`."""
        return dict(
            display_name=mlist.display_name,
            fqdn_listname=mlist.fqdn_listname,
            list_id=mlist.list_id,
            list_name=mlist.list_name,
            mail_host=mlist.mail_host,
            member_count=mlist.members.member_count,
            volume=mlist.volume,
            self_link=self.api.path_to('lists/{}'.format(mlist.list_id)),
            )

    def _get_collection(self, request):
        """See `CollectionMixin`."""
        return self._filter_lists(request)

    def _filter_lists(self, request, **kw):
        """Filter a collection using query parameters."""
        advertised = request.get_param_as_bool('advertised')
        if advertised:
            kw['advertised'] = True
        return getUtility(IListManager).find(**kw)


@public
class AList(_ListBase):
    """A mailing list."""

    def __init__(self, list_identifier):
        # list-id is preferred, but for backward compatibility, fqdn_listname
        # is also accepted.  If the string contains '@', treat it as the
        # latter.
        manager = getUtility(IListManager)
        if '@' in list_identifier:
            self._mlist = manager.get(list_identifier)
        else:
            self._mlist = manager.get_by_list_id(list_identifier)

    def on_get(self, request, response):
        """Return a single mailing list end-point."""
        if self._mlist is None:
            not_found(response)
        else:
            okay(response, self._resource_as_json(self._mlist))

    def on_delete(self, request, response):
        """Delete the named mailing list."""
        if self._mlist is None:
            not_found(response)
        else:
            remove_list(self._mlist)
            no_content(response)

    @child(member_matcher)
    def member(self, context, segments, role, email):
        """Return a single member representation."""
        if self._mlist is None:
            return NotFound(), []
        member = getUtility(ISubscriptionService).find_member(
            email, self._mlist.list_id, role)
        if member is None:
            return NotFound(), []
        return AMember(member.member_id)

    @child(roster_matcher)
    def roster(self, context, segments, role):
        """Return the collection of all a mailing list's members."""
        if self._mlist is None:
            return NotFound(), []
        return MembersOfList(self._mlist, role)

    @child(config_matcher)
    def config(self, context, segments, attribute=None):
        """Return a mailing list configuration object."""
        if self._mlist is None:
            return NotFound(), []
        return ListConfiguration(self._mlist, attribute)

    @child()
    def held(self, context, segments):
        """Return a list of held messages for the mailing list."""
        if self._mlist is None:
            return NotFound(), []
        return HeldMessages(self._mlist)

    @child()
    def requests(self, context, segments):
        """Return a list of subscription/unsubscription requests."""
        if self._mlist is None:
            return NotFound(), []
        return SubscriptionRequests(self._mlist)

    @child()
    def archivers(self, context, segments):
        """Return a representation of mailing list archivers."""
        if self._mlist is None:
            return NotFound(), []
        return ListArchivers(self._mlist)

    @child()
    def digest(self, context, segments):
        if self._mlist is None:
            return NotFound(), []
        return ListDigest(self._mlist)

    @child()
    def bans(self, context, segments):
        """Return a collection of mailing list's banned addresses."""
        if self._mlist is None:
            return NotFound(), []
        return BannedEmails(self._mlist)

    @child(r'^header-matches')
    def header_matches(self, context, segments):
        """Return a collection of mailing list's header matches."""
        if self._mlist is None:
            return NotFound(), []
        return HeaderMatches(self._mlist)

    @child()
    def uris(self, context, segments):
        """Return the template URIs of the mailing list.

        These are only available after API 3.0.
        """
        if self._mlist is None or self.api.version_info < (3, 1):
            return NotFound(), []
        if len(segments) == 0:
            return AllListURIs(self._mlist)
        if len(segments) > 1:
            return BadRequest(), []
        template = segments[0]
        if template not in AllListURIs.URIs:
            return NotFound(), []
        return AListURI(self._mlist, template), []


@public
class AllLists(_ListBase):
    """The mailing lists."""

    def on_post(self, request, response):
        """Create a new mailing list."""
        try:
            validator = Validator(fqdn_listname=str,
                                  style_name=str,
                                  _optional=('style_name',))
            mlist = create_list(**validator(request))
        except ListAlreadyExistsError:
            bad_request(response, b'Mailing list exists')
        except BadDomainSpecificationError as error:
            reason = 'Domain does not exist: {}'.format(error.domain)
            bad_request(response, reason.encode('utf-8'))
        except InvalidListNameError as error:
            reason = 'Invalid list name: {}'.format(error.listname)
            bad_request(response, reason.encode('utf-8'))
        except InvalidEmailAddressError as error:
            reason = 'Invalid list posting address: {}'.format(error.email)
            bad_request(response, reason.encode('utf-8'))
        else:
            location = self.api.path_to('lists/{0}'.format(mlist.list_id))
            created(response, location)

    def on_get(self, request, response):
        """/lists"""
        resource = self._make_collection(request)
        okay(response, etag(resource))


@public
class MembersOfList(MemberCollection):
    """The members of a mailing list."""

    def __init__(self, mailing_list, role):
        super().__init__()
        self._mlist = mailing_list
        self._role = role

    def _get_collection(self, request):
        """See `CollectionMixin`."""
        # Overrides _MemberBase._get_collection() because we only want to
        # return the members from the contexted roster.
        return getUtility(ISubscriptionService).find_members(
            list_id=self._mlist.list_id,
            role=self._role)

    def on_delete(self, request, response):
        """Delete the members of the named mailing list."""
        status = {}
        try:
            validator = Validator(emails=list_of_strings_validator)
            arguments = validator(request)
        except ValueError as error:
            bad_request(response, str(error))
            return
        emails = arguments.pop('emails')
        success, fail = getUtility(ISubscriptionService).unsubscribe_members(
            self._mlist.list_id, emails)
        # There should be no email in both sets.
        assert success.isdisjoint(fail), (success, fail)
        status.update({email: True for email in success})
        status.update({email: False for email in fail})
        okay(response, etag(status))


@public
class ListsForDomain(_ListBase):
    """The mailing lists for a particular domain."""

    def __init__(self, domain):
        self._domain = domain

    def on_get(self, request, response):
        """/domains/<domain>/lists"""
        resource = self._make_collection(request)
        okay(response, etag(resource))

    def _get_collection(self, request):
        """See `CollectionMixin`."""
        return self._filter_lists(request, mail_host=self._domain.mail_host)


@public
class ArchiverGetterSetter(GetterSetter):
    """Resource for updating archiver statuses."""

    def __init__(self, mlist):
        super().__init__()
        self._archiver_set = IListArchiverSet(mlist)

    def put(self, mlist, attribute, value):
        # attribute will contain the (bytes) name of the archiver that is
        # getting a new status.  value will be the representation of the new
        # boolean status.
        archiver = self._archiver_set.get(attribute)
        assert archiver is not None, attribute
        archiver.is_enabled = as_boolean(value)


@public
class ListArchivers:
    """The archivers for a list, with their enabled flags."""

    def __init__(self, mlist):
        self._mlist = mlist

    def on_get(self, request, response):
        """Get all the archiver statuses."""
        archiver_set = IListArchiverSet(self._mlist)
        resource = {archiver.name: archiver.is_enabled
                    for archiver in archiver_set.archivers
                    if archiver.system_archiver.is_enabled}
        okay(response, etag(resource))

    def patch_put(self, request, response, is_optional):
        archiver_set = IListArchiverSet(self._mlist)
        kws = {archiver.name: ArchiverGetterSetter(self._mlist)
               for archiver in archiver_set.archivers
               if archiver.system_archiver.is_enabled}
        if is_optional:
            # For a PATCH, all attributes are optional.
            kws['_optional'] = kws.keys()
        try:
            Validator(**kws).update(self._mlist, request)
        except ValueError as error:
            bad_request(response, str(error))
        else:
            no_content(response)

    def on_put(self, request, response):
        """Update all the archiver statuses."""
        self.patch_put(request, response, is_optional=False)

    def on_patch(self, request, response):
        """Patch some archiver statueses."""
        self.patch_put(request, response, is_optional=True)


@public
class ListDigest:
    """Simple resource representing actions on a list's digest."""

    def __init__(self, mlist):
        self._mlist = mlist

    def on_get(self, request, response):
        resource = dict(
            next_digest_number=self._mlist.next_digest_number,
            volume=self._mlist.volume,
            )
        okay(response, etag(resource))

    def on_post(self, request, response):
        try:
            validator = Validator(
                send=as_boolean,
                bump=as_boolean,
                _optional=('send', 'bump'))
            values = validator(request)
        except ValueError as error:
            bad_request(response, str(error))
            return
        if len(values) == 0:
            # There's nothing to do, but that's okay.
            okay(response)
            return
        if values.get('bump', False):
            bump_digest_number_and_volume(self._mlist)
        if values.get('send', False):
            maybe_send_digest_now(self._mlist, force=True)
        accepted(response)


@public
class Styles:
    """Simple resource representing all list styles."""

    def __init__(self):
        manager = getUtility(IStyleManager)
        style_names = sorted(style.name for style in manager.styles)
        self._resource = dict(
            style_names=style_names,
            default=config.styles.default)

    def on_get(self, request, response):
        okay(response, etag(self._resource))
