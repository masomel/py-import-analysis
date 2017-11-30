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

"""The root of the REST API."""

from mailman.config import config
from mailman.core.api import API30, API31
from mailman.core.constants import system_preferences
from mailman.core.system import system
from mailman.interfaces.listmanager import IListManager
from mailman.model.uid import UID
from mailman.rest.addresses import AllAddresses, AnAddress
from mailman.rest.bans import BannedEmail, BannedEmails
from mailman.rest.domains import ADomain, AllDomains
from mailman.rest.helpers import (
    BadRequest, NotFound, child, etag, no_content, not_found, okay)
from mailman.rest.lists import AList, AllLists, Styles
from mailman.rest.members import AMember, AllMembers, FindMembers
from mailman.rest.preferences import ReadOnlyPreferences
from mailman.rest.queues import AQueue, AQueueFile, AllQueues
from mailman.rest.templates import TemplateFinder
from mailman.rest.uris import ASiteURI, AllSiteURIs
from mailman.rest.users import AUser, AllUsers, ServerOwners
from public import public
from zope.component import getUtility


SLASH = '/'


@public
class Root:
    """The RESTful root resource.

    At the root of the tree are the API version numbers.  Everything else
    lives underneath those.  Currently there is only one API version number,
    and we start at 3.0 to match the Mailman version number.  That may not
    always be the case though.
    """

    @child('3.0')
    def api_version_30(self, context, segments):
        # API version 3.0 was introduced in Mailman 3.0.
        context['api'] = API30
        return TopLevel()

    @child('3.1')
    def api_version_31(self, context, segments):
        # API version 3.1 was introduced in Mailman 3.1.  Primary backward
        # incompatible difference is that uuids are represented as hex strings
        # instead of 128 bit integers.  The latter is not compatible with all
        # versions of JavaScript.
        context['api'] = API31
        return TopLevel()


@public
class Versions:
    def on_get(self, request, response):
        """/<api>/system/versions"""
        resource = dict(
            mailman_version=system.mailman_version,
            python_version=system.python_version,
            api_version=self.api.version,
            self_link=self.api.path_to('system/versions'),
            )
        okay(response, etag(resource))


@public
class SystemConfiguration:
    def __init__(self, section=None):
        self._section = section

    def on_get(self, request, response):
        if self._section is None:
            resource = dict(
                sections=sorted(section.name for section in config),
                self_link=self.api.path_to('system/configuration'),
                )
            okay(response, etag(resource))
            return
        missing = object()
        section = getattr(config, self._section, missing)
        if section is missing:
            not_found(response)
            return
        # Sections don't have .keys(), .values(), or .items() but we can
        # iterate over them.
        resource = {key: section[key] for key in section}
        # Add a `self_link` attribute to the resource.  This is a little ugly
        # because technically speaking we're mixing namespaces.  We can't have
        # a variable named `self_link` in any section, but also we can't have
        # `http_etag` either, so unless we want to shove all these values into
        # a sub dictionary (which we don't), we have to live with it.
        self_link = self.api.path_to(
            'system/configuration/{}'.format(section.name))
        resource['self_link'] = self_link
        okay(response, etag(resource))


@public
class Pipelines:
    def on_get(self, request, response):
        resource = dict(pipelines=sorted(config.pipelines))
        okay(response, etag(resource))


@public
class Chains:
    def on_get(self, request, response):
        resource = dict(chains=sorted(config.chains))
        okay(response, etag(resource))


@public
class Reserved:
    """Top level API for reserved operations.

    Nothing under this resource should be considered part of the stable API.
    The resources that appear here are purely for the support of external
    non-production systems, such as testing infrastructures for cooperating
    components.  Use at your own risk.
    """
    def __init__(self, segments):
        self._resource_path = SLASH.join(segments)

    def on_delete(self, request, response):
        if self._resource_path != 'uids/orphans':
            not_found(response)
            return
        UID.cull_orphans()
        no_content(response)


@public
class TopLevel:
    """Top level collections and entries."""

    @child()
    def system(self, context, segments):
        """/<api>/system"""
        if len(segments) == 0:
            # This provides backward compatibility; see /system/versions.
            return Versions()
        elif segments[0] == 'preferences':
            if len(segments) > 1:
                return BadRequest(), []
            return ReadOnlyPreferences(system_preferences, 'system'), []
        elif segments[0] == 'versions':
            if len(segments) > 1:
                return BadRequest(), []
            return Versions(), []
        elif segments[0] == 'configuration':
            if len(segments) <= 2:
                return SystemConfiguration(*segments[1:]), []
            return BadRequest(), []
        elif segments[0] == 'pipelines':
            if len(segments) > 1:
                return BadRequest(), []
            return Pipelines(), []
        elif segments[0] == 'chains':
            if len(segments) > 1:
                return BadRequest(), []
            return Chains(), []
        else:
            return NotFound(), []

    @child()
    def addresses(self, context, segments):
        """/<api>/addresses
           /<api>/addresses/<email>
        """
        if len(segments) == 0:
            return AllAddresses()
        else:
            email = segments.pop(0)
            return AnAddress(email), segments

    @child()
    def domains(self, context, segments):
        """/<api>/domains
           /<api>/domains/<domain>
        """
        if len(segments) == 0:
            return AllDomains()
        else:
            domain = segments.pop(0)
            return ADomain(domain), segments

    @child()
    def lists(self, context, segments):
        """/<api>/lists
           /<api>/lists/styles
           /<api>/lists/<list>
           /<api>/lists/<list>/...
        """
        if len(segments) == 0:
            return AllLists()
        # This does not prevent a mailing list being created with a short name
        # 'styles', since list identifiers (see below) must either be a
        # List-Id like styles.example.com, or an fqdn_listname like
        # styles@example.com.
        elif len(segments) == 1 and segments[0] == 'styles':
            return Styles(), []
        else:
            # list-id is preferred, but for backward compatibility,
            # fqdn_listname is also accepted.
            list_identifier = segments.pop(0)
            return AList(list_identifier), segments

    @child()
    def members(self, context, segments):
        """/<api>/members"""
        if len(segments) == 0:
            return AllMembers()
        # Either the next segment is the string "find" or a member id.  They
        # cannot collide.
        segment = segments.pop(0)
        if segment == 'find':
            resource = FindMembers()
        else:
            try:
                member_id = self.api.to_uuid(segment)
            except ValueError:
                member_id = None
            resource = AMember(member_id)
        return resource, segments

    @child()
    def users(self, context, segments):
        """/<api>/users"""
        if len(segments) == 0:
            return AllUsers()
        else:
            user_identifier = segments.pop(0)
            return AUser(user_identifier), segments

    @child()
    def owners(self, context, segments):
        """/<api>/owners"""
        if len(segments) != 0:
            return BadRequest(), []
        else:
            return ServerOwners(), segments

    @child()
    def templates(self, context, segments):
        """/<api>/templates/<fqdn_listname>/<template>/[<language>]

        Use content negotiation to context language and suffix (content-type).
        """
        # This resource is removed in API 3.1; use the /uris resource instead.
        if self.api.version_info > (3, 0):
            return NotFound(), []
        if len(segments) == 3:
            fqdn_listname, template, language = segments
        elif len(segments) == 2:
            fqdn_listname, template = segments
            language = 'en'
        else:
            return BadRequest(), []
        mlist = getUtility(IListManager).get(fqdn_listname)
        if mlist is None:
            return NotFound(), []
        # XXX dig out content-type from context.
        content_type = None
        return TemplateFinder(
            fqdn_listname, template, language, content_type)

    @child()
    def uris(self, content, segments):
        if self.api.version_info < (3, 1):
            return NotFound(), []
        if len(segments) == 0:
            return AllSiteURIs()
        if len(segments) > 1:
            return BadRequest(), []
        template = segments[0]
        if template not in AllSiteURIs.URIs:
            return NotFound(), []
        return ASiteURI(template), []

    @child()
    def queues(self, context, segments):
        """/<api>/queues[/<name>[/file]]"""
        if len(segments) == 0:
            return AllQueues()
        elif len(segments) == 1:
            return AQueue(segments[0]), []
        elif len(segments) == 2:
            return AQueueFile(segments[0], segments[1]), []
        else:
            return BadRequest(), []

    @child()
    def bans(self, context, segments):
        """/<api>/bans
           /<api>/bans/<email>
        """
        if len(segments) == 0:
            return BannedEmails(None)
        else:
            email = segments.pop(0)
            return BannedEmail(None, email), segments

    @child()
    def reserved(self, context, segments):
        """/<api>/reserved/[...]"""
        return Reserved(segments), []
