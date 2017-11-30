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

"""Test styles."""

import unittest

from mailman.interfaces.styles import (
    DuplicateStyleError, IStyle, IStyleManager)
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility
from zope.interface import implementer
from zope.interface.exceptions import DoesNotImplement


@implementer(IStyle)
class DummyStyle:

    name = 'dummy'
    priority = 1

    def apply(self, mlist):
        pass

    def match(self, mlist, styles):
        styles.append(self)


class TestStyle(unittest.TestCase):
    """Test styles."""

    layer = ConfigLayer

    def setUp(self):
        self.manager = getUtility(IStyleManager)

    def test_register_style_again(self):
        # Registering a style with the same name as a previous style raises an
        # exception.
        self.manager.register(DummyStyle())
        self.assertRaises(DuplicateStyleError,
                          self.manager.register, DummyStyle())

    def test_register_a_non_style(self):
        # You can't register something that doesn't implement the IStyle
        # interface.
        self.assertRaises(DoesNotImplement,
                          self.manager.register, object())

    def test_unregister_a_non_registered_style(self):
        # You cannot unregister a style that hasn't yet been registered.
        self.assertRaises(KeyError,
                          self.manager.unregister, DummyStyle())
