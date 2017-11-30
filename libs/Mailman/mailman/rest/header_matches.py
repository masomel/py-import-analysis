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

"""REST API for a mailing list's header matches."""

from mailman.interfaces.action import Action
from mailman.interfaces.mailinglist import IHeaderMatchList
from mailman.rest.helpers import (
    CollectionMixin, bad_request, child, created, etag, no_content, not_found,
    okay)
from mailman.rest.validator import Validator, enum_validator
from public import public


def lowercase(value):
    return str(value).lower()


class _HeaderMatchBase:
    """Common base class."""

    def __init__(self, mlist):
        self._mlist = mlist
        self.header_matches = IHeaderMatchList(self._mlist)

    def _location(self, position):
        return self.api.path_to('lists/{}/header-matches/{}'.format(
            self._mlist.list_id, position))

    def _resource_as_dict(self, header_match):
        """See `CollectionMixin`."""
        resource = dict(
            position=header_match.position,
            header=header_match.header,
            pattern=header_match.pattern,
            self_link=self._location(header_match.position),
            )
        if header_match.chain is not None:
            resource['action'] = header_match.chain
        return resource


@public
class HeaderMatch(_HeaderMatchBase):
    """A header match."""

    def __init__(self, mlist, position):
        super().__init__(mlist)
        self._position = position

    def on_get(self, request, response):
        """Get a header match."""
        try:
            header_match = self.header_matches[self._position]
        except IndexError:
            not_found(response, 'No header match at this position: {}'.format(
                      self._position))
        else:
            okay(response, etag(self._resource_as_dict(header_match)))

    def on_delete(self, request, response):
        """Remove a header match."""
        try:
            del self.header_matches[self._position]
        except IndexError:
            not_found(response, 'No header match at this position: {}'.format(
                      self._position))
        else:
            no_content(response)

    def _patch_put(self, request, response, is_optional):
        """Update the header match."""
        try:
            header_match = self.header_matches[self._position]
        except IndexError:
            not_found(response, 'No header match at this position: {}'.format(
                      self._position))
            return
        kws = dict(
            header=lowercase,
            pattern=str,
            position=int,
            action=enum_validator(Action),
            )
        if is_optional:
            # For a PATCH, all attributes are optional.
            kws['_optional'] = kws.keys()
        else:
            # For a PUT, position can remain unchanged and action can be None.
            kws['_optional'] = ('action', 'position')
        validator = Validator(**kws)
        try:
            arguments = validator(request)
            action = arguments.pop('action', None)
            if action is not None:
                arguments['chain'] = action.name
            for key, value in arguments.items():
                setattr(header_match, key, value)
        except ValueError as error:
            bad_request(response, str(error))
            return
        else:
            no_content(response)

    def on_put(self, request, response):
        """Full update of the header match."""
        self._patch_put(request, response, is_optional=False)

    def on_patch(self, request, response):
        """Partial update of the header match."""
        self._patch_put(request, response, is_optional=True)


@public
class HeaderMatches(_HeaderMatchBase, CollectionMixin):
    """The list of all header matches."""

    def _get_collection(self, request):
        """See `CollectionMixin`."""
        return list(self.header_matches)

    def on_get(self, request, response):
        """/header-matches"""
        resource = self._make_collection(request)
        okay(response, etag(resource))

    def on_post(self, request, response):
        """Add a header match."""
        validator = Validator(
            header=str,
            pattern=str,
            action=enum_validator(Action),
            _optional=('action',)
            )
        try:
            arguments = validator(request)
        except ValueError as error:
            bad_request(response, str(error))
            return
        action = arguments.pop('action', None)
        if action is not None:
            arguments['chain'] = action.name
        try:
            self.header_matches.append(**arguments)
        except ValueError:
            bad_request(response, b'This header match already exists')
        else:
            header_match = self.header_matches[-1]
            created(response, self._location(header_match.position))

    def on_delete(self, request, response):
        """Delete all header matches for this mailing list."""
        self.header_matches.clear()
        no_content(response)

    @child(r'^(?P<position>\d+)')
    def header_match(self, context, segments, **kw):
        return HeaderMatch(self._mlist, int(kw['position']))
