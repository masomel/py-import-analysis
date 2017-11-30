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

"""REST web service API contexts."""

from lazr.config import as_boolean
from mailman.config import config
from mailman.interfaces.api import IAPI
from public import public
from uuid import UUID
from zope.interface import implementer


@public
@implementer(IAPI)
class API30:
    version = '3.0'
    version_info = (3, 0)

    @classmethod
    def path_to(cls, resource):
        """See `IAPI`."""
        return '{}://{}:{}/{}/{}'.format(
            ('https' if as_boolean(config.webservice.use_https) else 'http'),
            config.webservice.hostname,
            config.webservice.port,
            cls.version,
            (resource[1:] if resource.startswith('/') else resource),
            )

    @staticmethod
    def from_uuid(uuid):
        """See `IAPI`."""
        return uuid.int

    @staticmethod
    def to_uuid(uuid):
        """See `IAPI`."""
        if isinstance(uuid, UUID):
            return uuid
        return UUID(int=int(uuid))


@public
@implementer(IAPI)
class API31:
    version = '3.1'
    version_info = (3, 1)

    @classmethod
    def path_to(cls, resource):
        """See `IAPI`."""
        return '{}://{}:{}/{}/{}'.format(
            ('https' if as_boolean(config.webservice.use_https) else 'http'),
            config.webservice.hostname,
            config.webservice.port,
            cls.version,
            (resource[1:] if resource.startswith('/') else resource),
            )

    @staticmethod
    def from_uuid(uuid):
        """See `IAPI`."""
        return uuid.hex

    @staticmethod
    def to_uuid(uuid):
        """See `IAPI`."""
        if isinstance(uuid, UUID):
            return uuid
        return UUID(hex=uuid)
