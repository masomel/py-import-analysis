# Copyright (C) 2008-2017 by the Free Software Foundation, Inc.
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

"""Interface for describing pipelines."""

from public import public
from zope.interface import Attribute, Interface


# For i18n extraction.
def _(s):
    return s


# These are thrown but they aren't exceptions so don't inherit from
# mailman.interfaces.errors.MailmanError.  Python requires that they inherit
# from BaseException.
@public
class DiscardMessage(BaseException):
    """The message can be discarded with no further action"""

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message


@public
class RejectMessage(BaseException):
    """The message will be bounced back to the sender"""

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message


@public
class IPipeline(Interface):
    """A pipeline of handlers."""

    name = Attribute('Pipeline name; must be unique.')
    description = Attribute('A brief description of this pipeline.')

    def __iter__():
        """Iterate over all the handlers in this pipeline."""
