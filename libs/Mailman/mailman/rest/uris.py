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

"""URI templates."""

from mailman.interfaces.template import ALL_TEMPLATES, ITemplateManager
from mailman.rest.helpers import (
    CollectionMixin, bad_request, etag, no_content, not_found, okay)
from mailman.rest.validator import Validator
from operator import attrgetter
from public import public
from zope.component import getUtility


class _URIBase(CollectionMixin):
    def __init__(self, context):
        self._context = context

    def _resource_as_dict(self, template):
        resource = dict(
            uri=template.uri,
            name=template.name,
            self_link=self.api.path_to('{}/uris/{}'.format(
                self._prefix, template.name)),
            )
        if template.username is not None and template.password is not None:
            resource['username'] = template.username
            resource['password'] = template.password
        return resource

    def _get_collection(self, request):
        manager = getUtility(ITemplateManager)
        collection = []
        for uri in self.URIs:
            template = manager.raw(uri, self._raw_context)
            if template is not None:
                collection.append(template)
        return sorted(collection, key=attrgetter('name'))

    def on_get(self, request, response):
        resource = self._make_collection(request)
        resource['self_link'] = self.api.path_to(
            '{}/uris'.format(self._prefix))
        okay(response, etag(resource))

    def _patch_put(self, request, response, is_optional):
        kws = {uri: str for uri in self.URIs}
        optionals = ['username', 'password']
        if is_optional:
            optionals.extend(self.URIs)
        # When PATCHing or PUTing all uris, a single optional
        # username/password applies to them all.
        kws['username'] = str
        kws['password'] = str
        kws['_optional'] = optionals
        try:
            arguments = Validator(**kws)(request)
        except ValueError as error:
            bad_request(response, str(error))
            return
        username = arguments.pop('username', None)
        password = arguments.pop('password', None)
        if not username and not password:
            # Normalize arguments.
            set_kws = {}
        elif username and password:
            # It's fine if both are specified.
            set_kws = dict(username=username, password=password)
        else:
            bad_request(response,
                        'Specify both username and password, or neither')
            return
        manager = getUtility(ITemplateManager)
        for key, value in arguments.items():
            if len(value) == 0:
                # The empty string is equivalent to DELETE.  Yeah, this isn't
                # very RESTful, but practicality beats purity.
                manager.delete(key, self._raw_context)
            else:
                manager.set(key, self._raw_context, value, **set_kws)
        no_content(response)

    def on_put(self, request, response):
        self._patch_put(request, response, is_optional=False)

    def on_patch(self, request, response):
        self._patch_put(request, response, is_optional=True)

    def on_delete(self, request, response):
        manager = getUtility(ITemplateManager)
        for uri in self.URIs:
            manager.delete(uri, self._raw_context)
        no_content(response)


class _ListURIBase(_URIBase):
    def __init__(self, context):
        super().__init__(context)
        self._raw_context = context.list_id
        self._prefix = 'lists/{}'.format(context.list_id)


@public
class AllListURIs(_ListURIBase):
    URIs = [name for name in ALL_TEMPLATES if name.startswith('list:')]

    def __init__(self, context):
        super().__init__(context)


@public
class AListURI(_ListURIBase):
    def __init__(self, context, template):
        super().__init__(context)
        self.URIs = [template]
        self._template = template

    def on_get(self, request, response):
        template = getUtility(ITemplateManager).raw(
            self._template, self._raw_context)
        if template is None:
            not_found(response)
        else:
            resource = dict(uri=template.uri)
            resource['self_link'] = self.api.path_to(
                '{}/uris/{}'.format(self._prefix, self._template))
            okay(response, etag(resource))


class _DomainURIBase(_URIBase):
    def __init__(self, context):
        super().__init__(context)
        self._raw_context = context.mail_host
        self._prefix = 'domains/{}'.format(context.mail_host)


@public
class AllDomainURIs(_DomainURIBase):
    URIs = [name for name in ALL_TEMPLATES
            if name.startswith('list:') or name.startswith('domain:')]


@public
class ADomainURI(_DomainURIBase):
    def __init__(self, context, template):
        super().__init__(context)
        self.URIs = [template]
        self._template = template

    def on_get(self, request, response):
        template = getUtility(ITemplateManager).raw(
            self._template, self._raw_context)
        if template is None:
            not_found(response)
        else:
            resource = dict(uri=template.uri)
            resource['self_link'] = self.api.path_to(
                '{}/uris/{}'.format(self._prefix, self._template))
            okay(response, etag(resource))


class _SiteURIBase(_URIBase):
    def __init__(self):
        super().__init__(None)
        self._raw_context = None
        self._prefix = ''


@public
class AllSiteURIs(_SiteURIBase):
    URIs = [name for name in ALL_TEMPLATES]


@public
class ASiteURI(_SiteURIBase):
    def __init__(self, template):
        super().__init__()
        self.URIs = [template]
        self._template = template

    def on_get(self, request, response):
        template = getUtility(ITemplateManager).raw(self._template, None)
        if template is None:
            not_found(response)
        else:
            resource = dict(uri=template.uri)
            resource['self_link'] = self.api.path_to(
                'uris/{}'.format(self._template))
            okay(response, etag(resource))
