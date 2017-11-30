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

"""The representation of a language."""


from mailman.interfaces.languages import ILanguage
from public import public
from zope.interface import implementer


@public
@implementer(ILanguage)
class Language:
    """The representation of a language."""

    def __init__(self, code, charset, description):
        self.code = code
        self.charset = charset
        self.description = description

    def __str__(self):
        return '<Language [{0.code}] {0.description}>'.format(self)

    __repr__ = __str__
