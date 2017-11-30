# Copyright (C) 2011-2017 by the Free Software Foundation, Inc.
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

"""Preferences."""

from lazr.config import as_boolean
from mailman.interfaces.member import DeliveryMode, DeliveryStatus
from mailman.rest.helpers import (
    GetterSetter, bad_request, etag, no_content, not_found, okay)
from mailman.rest.validator import (
    Validator, enum_validator, language_validator)
from public import public


PREFERENCES = (
    'acknowledge_posts',
    'delivery_mode',
    'delivery_status',
    'hide_address',
    'preferred_language',
    'receive_list_copy',
    'receive_own_postings',
    )


@public
class ReadOnlyPreferences:
    """.../<object>/preferences"""

    def __init__(self, parent, base_url):
        self._parent = parent
        self._base_url = base_url

    def on_get(self, request, response):
        resource = dict()
        for attr in PREFERENCES:
            # Handle this one specially.
            if attr == 'preferred_language':
                continue
            value = getattr(self._parent, attr, None)
            if value is not None:
                resource[attr] = value
        # Add the preferred language, if it's not missing.
        preferred_language = self._parent.preferred_language
        if preferred_language is not None:
            resource['preferred_language'] = preferred_language.code
        # Add the self link.
        resource['self_link'] = self.api.path_to(
            '{}/preferences'.format(self._base_url))
        okay(response, etag(resource))


@public
class Preferences(ReadOnlyPreferences):
    """Preferences which can be changed."""

    def patch_put(self, request, response, is_optional):
        if self._parent is None:
            not_found(response)
            return
        kws = dict(
            acknowledge_posts=GetterSetter(as_boolean),
            hide_address=GetterSetter(as_boolean),
            delivery_mode=GetterSetter(enum_validator(DeliveryMode)),
            delivery_status=GetterSetter(enum_validator(DeliveryStatus)),
            preferred_language=GetterSetter(language_validator),
            receive_list_copy=GetterSetter(as_boolean),
            receive_own_postings=GetterSetter(as_boolean),
            )
        if is_optional:
            # For a PUT, all attributes are optional.
            kws['_optional'] = kws.keys()
        try:
            Validator(**kws).update(self._parent, request)
        except ValueError as error:
            bad_request(response, str(error))
        else:
            no_content(response)

    def on_patch(self, request, response):
        """Patch the preferences."""
        self.patch_put(request, response, is_optional=True)

    def on_put(self, request, response):
        """Change all preferences."""
        self.patch_put(request, response, is_optional=False)

    def on_delete(self, request, response):
        """Delete all preferences."""
        for attr in PREFERENCES:
            if hasattr(self._parent, attr):
                setattr(self._parent, attr, None)
        no_content(response)
