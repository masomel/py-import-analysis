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

"""Test the string utilities."""

import unittest

from mailman.utilities import string


class TestString(unittest.TestCase):
    def test_oneline_bogus_charset(self):
        self.assertEqual(string.oneline('foo', 'bogus'), 'foo')

    def test_wrap_blank_paragraph(self):
        self.assertEqual(string.wrap('\n\n'), '\n\n')
