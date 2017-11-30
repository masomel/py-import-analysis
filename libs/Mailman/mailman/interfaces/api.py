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

"""REST web service API context."""

from public import public
from zope.interface import Attribute, Interface


@public
class IAPI(Interface):
    """The REST web service context."""

    version = Attribute(
        """The REST API version as a string.""")

    version_info = Attribute(
        """The REST API version as a tuple of integers.""")

    def path_to(resource):
        """Return the full REST URL to the given resource.

        :param resource: Resource path string without the leading scheme,
            host, port, or API version information.
        :type resource: str
        :return: Full URL path to the resource, with the scheme, host, port
            and API version prepended.
        :rtype: str
        """

    def from_uuid(uuid):
        """Return the string representation of a UUID.

        :param uuid: The UUID to convert.
        :type uuid: UUID
        :return: The string representation of the UUID, as appropriate for the
            API version.  In 3.0 this is the representation of an integer,
            while in 3.1 it is the hex representation.
        :rtype: str
        """

    def to_uuid(uuid):
        """Return the UUID from the string representation.

        :param uuid: A UUID, or the string representation of the UUID.
        :type uuid: UUID or str
        :return: The UUID, converted if needed as appropriate for the
            API version.  In 3.0, the string representation is
            interpreted as an integer, while in 3.1 it is the hex
            string.
        :rtype: UUID
        """
