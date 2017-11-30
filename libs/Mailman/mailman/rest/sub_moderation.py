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

"""REST API for held subscription requests."""

from mailman.app.moderator import send_rejection
from mailman.core.i18n import _
from mailman.interfaces.action import Action
from mailman.interfaces.member import AlreadySubscribedError
from mailman.interfaces.pending import IPendings
from mailman.interfaces.subscriptions import ISubscriptionManager
from mailman.rest.helpers import (
    CollectionMixin, bad_request, child, conflict, etag, no_content,
    not_found, okay)
from mailman.rest.validator import Validator, enum_validator
from public import public
from zope.component import getUtility


class _ModerationBase:
    """Common base class."""

    def __init__(self):
        self._pendings = getUtility(IPendings)

    def _resource_as_dict(self, token):
        pendable = self._pendings.confirm(token, expunge=False)
        if pendable is None:
            # This token isn't in the database.
            raise LookupError
        resource = dict(token=token)
        resource.update(pendable)
        return resource


@public
class IndividualRequest(_ModerationBase):
    """Resource for moderating a membership change."""

    def __init__(self, mlist, token):
        super().__init__()
        self._mlist = mlist
        self._registrar = ISubscriptionManager(self._mlist)
        self._token = token

    def on_get(self, request, response):
        # Get the pended record associated with this token, if it exists in
        # the pending table.
        try:
            resource = self._resource_as_dict(self._token)
            assert resource is not None, resource
        except LookupError:
            not_found(response)
            return
        okay(response, etag(resource))

    def on_post(self, request, response):
        try:
            validator = Validator(action=enum_validator(Action))
            arguments = validator(request)
        except ValueError as error:
            bad_request(response, str(error))
            return
        action = arguments['action']
        if action in (Action.defer, Action.hold):
            # At least see if the token is in the database.
            pendable = self._pendings.confirm(self._token, expunge=False)
            if pendable is None:
                not_found(response)
            else:
                no_content(response)
        elif action is Action.accept:
            try:
                self._registrar.confirm(self._token)
            except LookupError:
                not_found(response)
            except AlreadySubscribedError:
                conflict(response, 'Already subscribed')
            else:
                no_content(response)
        elif action is Action.discard:
            # At least see if the token is in the database.
            pendable = self._pendings.confirm(self._token, expunge=True)
            if pendable is None:
                not_found(response)
            else:
                no_content(response)
        else:
            assert action is Action.reject, action
            # Like discard but sends a rejection notice to the user.
            pendable = self._pendings.confirm(self._token, expunge=True)
            if pendable is None:
                not_found(response)
            else:
                no_content(response)
                send_rejection(
                    self._mlist, _('Subscription request'),
                    pendable['email'],
                    _('[No reason given]'))


@public
class SubscriptionRequests(_ModerationBase, CollectionMixin):
    """Resource for membership change requests."""

    def __init__(self, mlist):
        super().__init__()
        self._mlist = mlist

    def _get_collection(self, request):
        pendings = getUtility(IPendings).find(
            mlist=self._mlist, pend_type='subscription')
        return [token for token, pendable in pendings]

    def on_get(self, request, response):
        """/lists/listname/requests"""
        resource = self._make_collection(request)
        okay(response, etag(resource))

    @child(r'^(?P<token>[^/]+)')
    def subscription(self, context, segments, **kw):
        return IndividualRequest(self._mlist, kw['token'])
