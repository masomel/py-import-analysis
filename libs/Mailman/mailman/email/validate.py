# Copyright (C) 2009-2017 by the Free Software Foundation, Inc.
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

"""Email address validation."""

import re

from mailman.interfaces.address import (
    IEmailValidator, InvalidEmailAddressError)
from mailman.utilities.email import split_email
from public import public
from zope.interface import implementer


# What other characters should be allowed?
_valid_local = re.compile("[-0-9a-z!#$%&'*+./=?@_`{}~]", re.IGNORECASE)
# Strictly speaking, both ^ and | are allowed and others are allowed in quoted
# local parts, but this can open the door to certain web exploits so we don't
# allow them.
_valid_domain = re.compile('[-a-z0-9]', re.IGNORECASE)
# These are the only characters allowed in domain parts.


@public
@implementer(IEmailValidator)
class Validator:
    """An email address validator."""

    def is_valid(self, email):
        """See `IEmailValidator`."""
        if not email:
            return False
        user, domain_parts = split_email(email)
        if not user or len(_valid_local.sub('', user)) > 0:
            return False
        # Local, unqualified addresses are not allowed.
        if not domain_parts:
            return False
        if len(domain_parts) < 2:
            return False
        for p in domain_parts:
            if len(p) == 0 or p[0] == '-' or len(_valid_domain.sub('', p)) > 0:
                return False
        return True

    def validate(self, email):
        """Validate an email address.

        :param address: An email address.
        :type address: string
        :raise InvalidEmailAddressError: when the address is deemed invalid.
        """
        if not self.is_valid(email):
            raise InvalidEmailAddressError(email)
