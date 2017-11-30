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

"""Testing the password utility."""

import os
import unittest

from mailman.config import config
from mailman.testing.helpers import configuration
from mailman.testing.layers import ConfigLayer


class TestPasswords(unittest.TestCase):
    layer = ConfigLayer

    def test_default_passlib(self):
        # By default, testing uses the roundup_plaintext hash algorithm, which
        # is just plaintext with a prefix.
        self.assertEqual(config.password_context.encrypt('my password'),
                         '{plaintext}my password')

    def test_passlib_from_file_path(self):
        # Set up this test to use a passlib configuration file specified with
        # a file system path.  We prove we're using the new configuration
        # because a non-prefixed, i.e. non-roundup, plaintext hash algorithm
        # will be used.  When a file system path is used, the file can end in
        # any suffix.
        config_file = os.path.join(config.VAR_DIR, 'passlib.config')
        with open(config_file, 'w') as fp:
            print("""\
[passlib]
schemes = plaintext
""", file=fp)
        with configuration('passwords', configuration=config_file):
            self.assertEqual(config.password_context.encrypt('my password'),
                             'my password')
