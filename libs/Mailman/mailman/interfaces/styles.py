# Copyright (C) 2007-2017 by the Free Software Foundation, Inc.
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

"""Interfaces for list styles."""

from mailman.interfaces.errors import MailmanError
from public import public
from zope.interface import Attribute, Interface


@public
class DuplicateStyleError(MailmanError):
    """A style with the same name is already registered."""


@public
class IStyle(Interface):
    """Application of a style to an existing mailing list."""

    name = Attribute(
        """The name of this style.  Must be unique.""")

    def apply(mailing_list):
        """Apply the style to the mailing list.

        :type mailing_list: `IMailingList`.
        :param mailing_list: the mailing list to apply the style to.
        """


@public
class IStyleManager(Interface):
    """A manager of styles."""

    def get(name):
        """Return the named style or None.

        :type name: string
        :param name: A style name.
        :return: the named `IStyle` or None if the style doesn't exist.
        """

    styles = Attribute(
        'An iterator over all the styles known by this manager.')

    def populate():
        """Populate the styles from the configuration files.

        This clears the current set of styles and resets them from those
        defined in the configuration files.
        """

    def register(style):
        """Register a style with this manager.

        :param style: an IStyle.
        :raises DuplicateStyleError: if a style with the same name was already
            registered.
        """

    def unregister(style):
        """Unregister the style.

        :param style: an IStyle.
        :raises KeyError: If the style's name is not currently registered.
        """
