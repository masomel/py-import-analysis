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

"""Test the MHonArc archiver."""

import os
import sys
import shutil
import tempfile
import unittest

from mailman.app.lifecycle import create_list
from mailman.archiving.mhonarc import MHonArc
from mailman.database.transaction import transaction
from mailman.testing.helpers import (
    configuration, specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from pkg_resources import resource_filename


class TestMhonarc(unittest.TestCase):
    """Test the MHonArc archiver."""

    layer = ConfigLayer

    def setUp(self):
        # Create a fake mailing list and message object.
        self._msg = mfs("""\
To: test@example.com
From: anne@example.com
Subject: Testing the test list
Message-ID: <ant>
Message-ID-Hash: MS6QLWERIJLGCRF44J7USBFDELMNT2BW

Tests are better than no tests
but the water deserves to be swum.
""")
        with transaction():
            self._mlist = create_list('test@example.com')
        tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tempdir)
        # Here's the command to execute our fake MHonArc process.
        shutil.copy(
            resource_filename('mailman.archiving.tests', 'fake_mhonarc.py'),
            tempdir)
        self._output_file = os.path.join(tempdir, 'output.txt')
        command = '{} {} {}'.format(
            sys.executable,
            os.path.join(tempdir, 'fake_mhonarc.py'),
            self._output_file)
        # Write an external configuration file which points the command at our
        # fake MHonArc process.
        self._cfg = os.path.join(tempdir, 'mhonarc.cfg')
        with open(self._cfg, 'w', encoding='utf-8') as fp:
            print("""\
[general]
base_url: http://$hostname/archives/$fqdn_listname
command: {command}
""".format(command=command), file=fp)

    def test_mhonarc(self):
        # The archiver properly sends stdin to the subprocess.
        with configuration('archiver.mhonarc',
                           configuration=self._cfg,
                           enable='yes'):
            MHonArc().archive_message(self._mlist, self._msg)
        with open(self._output_file, 'r', encoding='utf-8') as fp:
            results = fp.read().splitlines()
        self.assertEqual(results[0], '<ant>')
        self.assertEqual(results[1], 'MS6QLWERIJLGCRF44J7USBFDELMNT2BW')
