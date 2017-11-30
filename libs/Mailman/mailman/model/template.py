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

"""Template management."""

import logging

from mailman.config import config
from mailman.database.model import Model
from mailman.database.transaction import dbconnection
from mailman.database.types import SAUnicode
from mailman.interfaces.cache import ICacheManager
from mailman.interfaces.domain import IDomain
from mailman.interfaces.mailinglist import IMailingList
from mailman.interfaces.template import (
    ALL_TEMPLATES, ITemplateLoader, ITemplateManager)
from mailman.utilities import protocols
from mailman.utilities.i18n import find
from mailman.utilities.string import expand
from public import public
from requests import HTTPError
from sqlalchemy import Column, Integer
from urllib.error import URLError
from urllib.parse import urlparse
from zope.component import getUtility
from zope.interface import implementer


COMMASPACE = ', '
log = logging.getLogger('mailman.http')


class Template(Model):
    __tablename__ = 'template'

    id = Column(Integer, primary_key=True)
    name = Column(SAUnicode)
    context = Column(SAUnicode)
    uri = Column(SAUnicode)
    username = Column(SAUnicode, nullable=True)
    password = Column(SAUnicode, nullable=True)

    def __init__(self, name, context, uri, username, password):
        self.name = name
        self.context = context
        self.reset(uri, username, password)

    def reset(self, uri, username, password):
        self.uri = uri
        self.username = username
        self.password = password


@public
@implementer(ITemplateManager)
class TemplateManager:
    """Manager of templates, with caching and support for mailman:// URIs."""

    @dbconnection
    def set(self, store, name, context, uri, username=None, password=''):
        """See `ITemplateManager`."""
        # Just record the fact that we have a template set.  Make sure that if
        # there is an existing template with the same context and name, we
        # override any of its settings (and evict the cache).
        template = store.query(Template).filter(
            Template.name == name,
            Template.context == context).one_or_none()
        if template is None:
            template = Template(name, context, uri, username, password)
            store.add(template)
        else:
            template.reset(uri, username, password)

    @dbconnection
    def get(self, store, name, context, **kws):
        """See `ITemplateManager`."""
        template = store.query(Template).filter(
            Template.name == name,
            Template.context == context).one_or_none()
        if template is None:
            return None
        actual_uri = expand(template.uri, None, kws)
        cache_mgr = getUtility(ICacheManager)
        contents = cache_mgr.get(actual_uri)
        if contents is None:
            # It's likely that the cached contents have expired.
            auth = {}
            if template.username is not None:
                auth['auth'] = (template.username, template.password)
            try:
                contents = protocols.get(actual_uri, **auth)
            except HTTPError as error:
                # 404/NotFound errors are interpreted as missing templates,
                # for which we'll return the default (i.e. the empty string).
                # All other exceptions get passed up the chain.
                if error.response.status_code != 404:
                    raise
                log.exception('Cannot retrieve template at {} ({})'.format(
                    actual_uri, auth.get('auth', '<no authorization>')))
                return ''
            # We don't need to cache mailman: contents since those are already
            # on the file system.
            if urlparse(actual_uri).scheme != 'mailman':
                cache_mgr.add(actual_uri, contents)
        return contents

    @dbconnection
    def raw(self, store, name, context):
        """See `ITemplateManager`."""
        return store.query(Template).filter(
            Template.name == name,
            Template.context == context).one_or_none()

    @dbconnection
    def delete(self, store, name, context):
        """See `ITemplateManager`."""
        template = store.query(Template).filter(
            Template.name == name,
            Template.context == context).one_or_none()
        if template is not None:
            store.delete(template)
        # We don't clear the cache entry, we just let it expire.


@public
@implementer(ITemplateLoader)
class TemplateLoader:
    """Loader of templates."""

    def get(self, name, context=None, **kws):
        """See `ITemplateLoader`."""
        # Gather some additional information based on the context.
        substitutions = {}
        if IMailingList.providedBy(context):
            mlist = context
            domain = context.domain
            lookup_contexts = [
                mlist.list_id,
                mlist.mail_host,
                None,
                ]
            substitutions.update(dict(
                list_id=mlist.list_id,
                # For backward compatibility, we call this $listname.
                listname=mlist.fqdn_listname,
                domain_name=domain.mail_host,
                language=mlist.preferred_language.code,
                ))
        elif IDomain.providedBy(context):
            mlist = None
            domain = context
            lookup_contexts = [
                domain.mail_host,
                None,
                ]
            substitutions['domain_name'] = domain.mail_host
        elif context is None:
            mlist = domain = None
            lookup_contexts = [None]
        else:
            raise ValueError('Bad context type: {!r}'.format(context))
        # The passed in keyword arguments take precedence.
        substitutions.update(kws)
        # See if there's a cached template registered for this name and
        # context, passing in the url substitutions.  This handles http:,
        # https:, and file: urls.
        for lookup_context in lookup_contexts:
            try:
                contents = getUtility(ITemplateManager).get(
                    name, lookup_context, **substitutions)
            except (HTTPError, URLError):
                pass
            else:
                if contents is not None:
                    return contents
        # Fallback to searching within the source code.
        code = substitutions.get('language', config.mailman.default_language)
        # Find the template, mutating any missing template exception.
        missing = object()
        default_uri = ALL_TEMPLATES.get(name, missing)
        if default_uri is None:
            return ''
        elif default_uri is missing:
            raise URLError('No such file')
        path, fp = find(default_uri, mlist, code)
        try:
            return fp.read()
        finally:
            fp.close()
