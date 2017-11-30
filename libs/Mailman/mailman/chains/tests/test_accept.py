# Copyright (C) 2016-2017 by the Free Software Foundation, Inc.
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

"""Test the accept chain."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.chains.base import Link
from mailman.config import config
from mailman.core.chains import process as process_chain
from mailman.interfaces.chain import AcceptEvent, IChain, LinkAction
from mailman.testing.helpers import (
    event_subscribers, specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from zope.interface import implementer


@implementer(IChain)
class MyChain:
    name = 'mine'
    description = 'A test chain'

    def get_links(self, mlist, msg, msgdata):
        def set_hits(mlist, msg, msgdata):
            msgdata['rule_hits'] = ['first', 'second', 'third']
        yield Link('truth', LinkAction.run, function=set_hits)
        yield Link('truth', LinkAction.jump, 'accept')


class TestAccept(unittest.TestCase):
    """Test the accept chain."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: Ignore

""")

    def test_rule_hits(self):
        config.chains['mine'] = MyChain()
        self.addCleanup(config.chains.pop, 'mine')
        hits = None
        def handler(event):                                # noqa: E306
            nonlocal hits
            if isinstance(event, AcceptEvent):
                hits = event.msg['x-mailman-rule-hits']
        with event_subscribers(handler):
            process_chain(self._mlist, self._msg, {}, start_chain='mine')
        self.assertEqual(hits, 'first; second; third')
