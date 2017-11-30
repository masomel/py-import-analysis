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

"""Template downloader with cache."""

from public import public
from zope.interface import Attribute, Interface


@public
class ITemplate(Interface):
    """A template record."""

    name = Attribute("""The template name.""")

    context = Attribute("""\
        The template context.  This may be a list-id, a domain mail host name,
        or None (for the global context).
        """)

    uri = Attribute("""The template uri.""")

    username = Attribute("""\
        Optional username used to retrieved the contents referenced by the
        template uri.  This can be None if no username/password is needed.""")

    password = Attribute("""\
        Optional password used to retrieved the contents referenced by the
        template uri.  This can be None if no username/password is needed.""")


@public
class ITemplateLoader(Interface):
    """The template downloader utility."""

    def get(name, context=None, **kws):
        """Find the named template for the given context.

        This search for a named template using a stacked strategy.  If the
        template has been registered for the given context in the template
        manager, that template is used.  If not, a file system based template
        is used as a fallback.  If nothing can be found, the empty string is
        returned.

        Use the ``ITemplateManager`` to set specific template locations.  The
        fallbacks all use the ``mailman:`` scheme to use in-tree defaults.

        :param name: The name of the template to find.
        :type name: str
        :param context: The context in which to find the template.  This can
            be either an IMailingList, an IDomain, or None for the global/site
            context.  The template will be searched in order from most
            specific to least specific, i.e. from list-id, to domain, to
            global.
        :type context: IMailingList, IDomain, None
        :param kws: Additional URL substitution variables.  Once a URL for the
            given name and context is identified, these are used to fill in
            placeholders in the URL before the template is retrieved.
            `list_id`, `list_name`, and `mail_host` will automatically be
            filled in if available depending on the `context`.  This
            dictionary is passed directly to the underlying
            ``ITemplatemanager.get()`` call.
        :type kws: dict
        :return: The found template or its fallback.
        :rtype: str
        """


@public
class ITemplateManager(Interface):
    """Manager/loader for notification templates."""

    def set(name, context, uri, username=None, password=''):
        """Set a template mapping from name to URI.

        The URI may be cached for some length of time defined by the system.

        :param name: The template name, including any extension.
        :type name: str
        :param context: The context for this name->URI mapping.  This can be a
            list-id, domain mail host name, or None (for global context).
        :type context: str
        :param uri: The URI of the template.  Normal http: and https: URIs can
            be used, as well as special mailman: URIs which reference internal
            resources.
        :type uri: str
        :param username: Optional user name for Basic Auth on the URI.
        :type username: str
        :param password: Optional password for Basic Auth on the URI.
        :type username: str
        """

    def get(name, context, **kws):
        """Return the contents for the given context and name.

        `context` can be a list-id, domain mail host name, or "*" (for global
        context).  A search will be performed from the named context up to the
        global context.  For example, if a List-Id is given but no template
        for that mailing list under that name is registered, the mailing
        list's domain is search, then the global context is searched.

        If the URI mapped to this mailing list/name pair is not yet retrieved,
        it is downloaded first.  If the cache lifetime has expired, it will be
        downloaded again.  Otherwise the cached version will be returned.

        :param name: The template name, including any extension.
        :type name: str
        :param context: The context for this name->URI mapping.  This can be a
            List-ID, domain mail host name, or None (for global context).
        :type context: str
        :param kws: A substitution dictionary that is interpolated into the
            url to retrieve the contents of the template.  Passing in a
            different dictionary than before can cause a new template to be
            downloaded.
        :type kws: dict
        :return: The resource mapped to the given name, or None if not found.
        :rtype: str or None
        """

    def raw(name, context):
        """Return the raw template information for the given context and name.

        `context` can be a list-id, domain mail host name, or "*" (for global
        context).  The raw template matching the given name and context is
        returned, otherwise None if no such template has been registered.

        :param name: The template name, including any extension.
        :type name: str
        :param context: The context for this name->URI mapping.  This can be a
            List-ID, domain mail host name, or None (for global context).
        :type context: str
        :return: The raw template record, or None if not found.
        :rtype: ITemplate or None
        """

    def delete(name, context):
        """Delete the named template and any cached contents.

        :param name: The template name, including any extension.
        :type name: str
        :param context: The context for this name->URI mapping.  This can be a
            List-ID, domain mail host name, or None (for global context).
        :type context: str
        """


# Mapping of template names to their in-source file names.  A None value means
# that there is no file in the tree for that template.

ALL_TEMPLATES = {
    key: '{}.txt'.format(key)
    for key in {
        'domain:admin:notice:new-list',
        'list:admin:action:post',
        'list:admin:action:subscribe',
        'list:admin:action:unsubscribe',
        'list:admin:notice:subscribe',
        'list:admin:notice:unrecognized',
        'list:admin:notice:unsubscribe',
        'list:member:digest:masthead',
        'list:user:action:subscribe',
        'list:user:action:unsubscribe',
        'list:user:notice:hold',
        'list:user:notice:no-more-today',
        'list:user:notice:post',
        'list:user:notice:probe',
        'list:user:notice:refuse',
        'list:user:notice:welcome',
        }
    }

# These have other names.
ALL_TEMPLATES.update({
    'list:member:digest:footer': 'list:member:generic:footer.txt',
    'list:member:regular:footer': 'list:member:generic:footer.txt',
    })

# These are some extra supported templates which don't have a mapping to a
# file in the source tree.
ALL_TEMPLATES.update({
    'list:member:digest:header': None,
    'list:member:regular:header': None,
    'list:user:notice:goodbye':  None,
    })

public(ALL_TEMPLATES=ALL_TEMPLATES)
