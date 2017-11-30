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

"""A wrapper around passlib."""

from mailman.config.config import load_external
from mailman.interfaces.configuration import ConfigurationUpdatedEvent
from passlib.context import CryptContext
from public import public


class PasswordContext:
    def __init__(self, config):
        """Create a password context for hashing and verification.

        :param config: The `IConfiguration` instance.
        """
        config_string = load_external(config.passwords.configuration)
        self._context = CryptContext.from_string(config_string)

    def encrypt(self, secret):
        """Return the secret, hashed using the current password context.

        :param secret: The plain text password.
        :type secret: string
        :return: The hashed secret.
        :rtype: string
        """
        return self._context.encrypt(secret)

    def verify(self, password, hashed):
        """Verify the hashed password and return the updated hash.

        This is essentially a wrapper around
        `passlib.CryptContext.verify_and_update()` using only the first two
        arguments.

        :param password: The plain text secret provided by the user.
        :type password:
        :param hashed: The hash string to compare to.
        :type hashed: string
        :return: 2-tuple where the first element is a flag indicating whether
            the password verified or not, and the second value whether the
            existing hash needs to be replaced (a str if so, else None).
        :rtype: 2-tuple
        """
        return self._context.verify_and_update(password, hashed)


@public
def handle_ConfigurationUpdatedEvent(event):
    if isinstance(event, ConfigurationUpdatedEvent):
        # Just reset the password context.
        event.config.password_context = PasswordContext(event.config)
