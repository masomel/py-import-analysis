# Copyright (C) 2015-2017 by the Free Software Foundation, Inc.
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

"""<api>/queues."""

from mailman.app.inject import inject_text
from mailman.config import config
from mailman.interfaces.listmanager import IListManager
from mailman.rest.helpers import (
    CollectionMixin, bad_request, created, etag, no_content, not_found, okay)
from mailman.rest.validator import Validator
from public import public
from zope.component import getUtility


class _QueuesBase(CollectionMixin):
    """Shared base class for queues."""

    def _resource_as_dict(self, name):
        """See `CollectionMixin`."""
        switchboard = config.switchboards[name]
        files = switchboard.files
        return dict(
            name=switchboard.name,
            directory=switchboard.queue_directory,
            count=len(files),
            files=files,
            self_link=self.api.path_to('queues/{}'.format(name)),
            )

    def _get_collection(self, request):
        """See `CollectionMixin`."""
        return sorted(config.switchboards)


@public
class AQueue(_QueuesBase):
    """A single queue."""

    def __init__(self, name):
        self._name = name

    def on_get(self, request, response):
        """Return a single queue resource."""
        if self._name not in config.switchboards:
            not_found(response)
        else:
            okay(response, self._resource_as_json(self._name))

    def on_post(self, request, response):
        """Inject a message into the queue."""
        try:
            validator = Validator(list_id=str,
                                  text=str)
            values = validator(request)
        except ValueError as error:
            bad_request(response, str(error))
            return
        list_id = values['list_id']
        mlist = getUtility(IListManager).get_by_list_id(list_id)
        if mlist is None:
            bad_request(response, 'No such list: {}'.format(list_id))
            return
        try:
            filebase = inject_text(
                mlist, values['text'], switchboard=self._name)
        except Exception as error:
            bad_request(response, str(error))
            return
        else:
            location = self.api.path_to(
                'queues/{}/{}'.format(self._name, filebase))
            created(response, location)


@public
class AQueueFile:
    def __init__(self, name, filebase):
        self._name = name
        self._filebase = filebase

    def on_delete(self, request, response):
        """Delete the queue file."""
        switchboard = config.switchboards.get(self._name)
        if switchboard is None:
            not_found(response, 'No such queue: {}'.format(self._name))
            return
        try:
            switchboard.dequeue(self._filebase)
        except FileNotFoundError:
            not_found(response,
                      'No such queue file: {}'.format(self._filebase))
        else:
            no_content(response)


@public
class AllQueues(_QueuesBase):
    """All queues."""

    def on_get(self, request, response):
        """<api>/queues"""
        resource = self._make_collection(request)
        resource['self_link'] = self.api.path_to('queues')
        okay(response, etag(resource))
