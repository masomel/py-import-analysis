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

"""REST for domains."""

from mailman.interfaces.domain import (
    BadDomainSpecificationError, IDomainManager)
from mailman.rest.helpers import (
    BadRequest, CollectionMixin, GetterSetter, NotFound, bad_request, child,
    created, etag, no_content, not_found, okay)
from mailman.rest.lists import ListsForDomain
from mailman.rest.uris import ADomainURI, AllDomainURIs
from mailman.rest.users import ListOfDomainOwners, OwnersForDomain
from mailman.rest.validator import Validator, list_of_strings_validator
from public import public
from zope.component import getUtility


class _DomainBase(CollectionMixin):
    """Shared base class for domain representations."""

    def _resource_as_dict(self, domain):
        """See `CollectionMixin`."""
        return dict(
            description=domain.description,
            mail_host=domain.mail_host,
            self_link=self.api.path_to('domains/{}'.format(domain.mail_host)),
            )

    def _get_collection(self, request):
        """See `CollectionMixin`."""
        return list(getUtility(IDomainManager))


@public
class ADomain(_DomainBase):
    """A domain."""

    def __init__(self, domain):
        self._domain = domain

    def on_get(self, request, response):
        """Return a single domain end-point."""
        domain = getUtility(IDomainManager).get(self._domain)
        if domain is None:
            not_found(response)
        else:
            okay(response, self._resource_as_json(domain))

    def on_delete(self, request, response):
        """Delete the domain."""
        try:
            getUtility(IDomainManager).remove(self._domain)
        except KeyError:
            # The domain does not exist.
            not_found(response)
        else:
            no_content(response)

    def patch_put(self, request, response, is_optional):
        domain = getUtility(IDomainManager).get(self._domain)
        if domain is None:
            not_found(response)
        kws = dict(
            description=GetterSetter(str),
            owner=ListOfDomainOwners(list_of_strings_validator),
            )
        if is_optional:
            # For a PATCH, all attributes are optional.
            kws['_optional'] = kws.keys()
        try:
            Validator(**kws).update(domain, request)
        except ValueError as error:
            bad_request(response, str(error))
        else:
            no_content(response)

    def on_put(self, request, response):
        """Update all the domain except mail_host"""
        self.patch_put(request, response, is_optional=False)

    def on_patch(self, request, response):
        """Patch some domain attributes."""
        self.patch_put(request, response, is_optional=True)

    @child()
    def lists(self, context, segments):
        """/domains/<domain>/lists"""
        if len(segments) == 0:
            domain = getUtility(IDomainManager).get(self._domain)
            if domain is None:
                return NotFound()
            return ListsForDomain(domain)
        else:
            return BadRequest(), []

    @child()
    def owners(self, context, segments):
        """/domains/<domain>/owners"""
        if len(segments) == 0:
            domain = getUtility(IDomainManager).get(self._domain)
            if domain is None:
                return NotFound()
            return OwnersForDomain(domain)
        else:
            return NotFound(), []

    @child()
    def uris(self, context, segments):
        """Return the template URIs of the domain.

        These are only available after API 3.0.
        """
        domain = getUtility(IDomainManager).get(self._domain)
        if domain is None or self.api.version_info < (3, 1):
            return NotFound(), []
        if len(segments) == 0:
            return AllDomainURIs(domain)
        if len(segments) > 1:
            return BadRequest(), []
        template = segments[0]
        if template not in AllDomainURIs.URIs:
            return NotFound(), []
        return ADomainURI(domain, template), []


@public
class AllDomains(_DomainBase):
    """The domains."""

    def on_post(self, request, response):
        """Create a new domain."""
        domain_manager = getUtility(IDomainManager)
        try:
            validator = Validator(mail_host=str,
                                  description=str,
                                  owner=list_of_strings_validator,
                                  _optional=('description', 'owner'))
            values = validator(request)
            # For consistency, owners are passed in as multiple `owner` keys,
            # but .add() requires an `owners` keyword.  Match impedence.
            owners = values.pop('owner', None)
            if owners is not None:
                values['owners'] = owners
            domain = domain_manager.add(**values)
        except BadDomainSpecificationError as error:
            bad_request(response, str(error))
        else:
            location = self.api.path_to('domains/{}'.format(domain.mail_host))
            created(response, location)

    def on_get(self, request, response):
        """/domains"""
        resource = self._make_collection(request)
        okay(response, etag(resource))
