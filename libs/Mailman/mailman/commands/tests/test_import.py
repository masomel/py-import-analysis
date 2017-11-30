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

"""Test the `mailman import21` subcommand."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.commands.cli_import import Import21
from mailman.testing.layers import ConfigLayer
from pkg_resources import resource_filename
from unittest.mock import patch


class FakeArgs:
    listname = ['test@example.com']
    pickle_file = [
        resource_filename('mailman.testing', 'config-with-instances.pck'),
        ]


class TestImport(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self.command = Import21()
        self.args = FakeArgs()
        self.mlist = create_list('test@example.com')

    @patch('mailman.commands.cli_import.import_config_pck')
    def test_process_pickle_with_bounce_info(self, import_config_pck):
        # The sample data contains Mailman 2 bounce info, represented as
        # _BounceInfo instances.  We throw these away when importing to
        # Mailman 3, but we have to fake the instance's classes, otherwise
        # unpickling the dictionaries will fail.
        try:
            self.command.process(self.args)
        except ImportError as error:
            self.fail('The pickle failed loading: {}'.format(error))
        self.assertTrue(import_config_pck.called)
