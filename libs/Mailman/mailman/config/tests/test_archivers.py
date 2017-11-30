# Copyright (C) 2013-2017 by the Free Software Foundation, Inc.
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

"""Site-wide archiver configuration tests."""

import unittest

from mailman.config import config
from mailman.testing.helpers import configuration
from mailman.testing.layers import ConfigLayer


class TestArchivers(unittest.TestCase):
    layer = ConfigLayer

    def test_enabled(self):
        # By default, the testing configuration enables some archivers.
        archivers = {}
        for archiver in config.archivers:
            archivers[archiver.name] = archiver
        self.assertFalse(archivers['prototype'].is_enabled)
        self.assertTrue(archivers['mail-archive'].is_enabled)
        self.assertTrue(archivers['mhonarc'].is_enabled)

    @configuration('archiver.mhonarc', enable='no')
    def test_disabled(self):
        # We just disabled one of the archivers.
        archivers = {}
        for archiver in config.archivers:
            archivers[archiver.name] = archiver
        self.assertFalse(archivers['prototype'].is_enabled)
        self.assertTrue(archivers['mail-archive'].is_enabled)
        self.assertFalse(archivers['mhonarc'].is_enabled)
