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

"""Style manager."""

from mailman.interfaces.configuration import ConfigurationUpdatedEvent
from mailman.interfaces.styles import (
    DuplicateStyleError, IStyle, IStyleManager)
from mailman.utilities.modules import find_components
from public import public
from zope.component import getUtility
from zope.interface import implementer
from zope.interface.verify import verifyObject


@public
@implementer(IStyleManager)
class StyleManager:
    """The built-in style manager."""

    def __init__(self):
        """Install all styles from the configuration files."""
        self._styles = {}

    def populate(self):
        self._styles.clear()
        # Avoid circular imports.
        from mailman.config import config
        # Calculate the Python import paths to search.
        paths = filter(None, (path.strip()
                              for path in config.styles.paths.splitlines()))
        for path in paths:
            for style_class in find_components(path, IStyle):
                style = style_class()
                verifyObject(IStyle, style)
                assert style.name not in self._styles, (
                    'Duplicate style "{}" found in {}'.format(
                        style.name, style_class))
                self._styles[style.name] = style

    def get(self, name):
        """See `IStyleManager`."""
        return self._styles.get(name)

    @property
    def styles(self):
        """See `IStyleManager`."""
        for style_name in sorted(self._styles):
            yield self._styles[style_name]

    def register(self, style):
        """See `IStyleManager`."""
        verifyObject(IStyle, style)
        if style.name in self._styles:
            raise DuplicateStyleError(style.name)
        self._styles[style.name] = style

    def unregister(self, style):
        """See `IStyleManager`."""
        # Let KeyErrors percolate up.
        del self._styles[style.name]


@public
def handle_ConfigurationUpdatedEvent(event):
    if isinstance(event, ConfigurationUpdatedEvent):
        getUtility(IStyleManager).populate()
