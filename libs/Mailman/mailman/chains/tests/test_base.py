# Copyright (C) 2014-2017 by the Free Software Foundation, Inc.
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

"""Test the base chain stuff."""

import unittest

from mailman.chains.accept import AcceptChain
from mailman.chains.base import Chain, Link, TerminalChainBase
from mailman.interfaces.chain import LinkAction
from mailman.rules.any import Any
from mailman.testing.layers import ConfigLayer


class SimpleChain(TerminalChainBase):
    def _process(self, mlist, msg, msgdata):
        pass


class TestMiscellaneous(unittest.TestCase):
    """Reach additional code coverage."""

    def test_link_repr(self):
        self.assertEqual(
            repr(Link(Any())), '<Link "if any then LinkAction.defer">')

    def test_link_repr_function(self):
        def function():
            pass
        self.assertEqual(
            repr(Link(Any(), function=function)),
            '<Link "if any then LinkAction.defer" function()>')

    def test_link_repr_chain(self):
        self.assertEqual(
            repr(Link(Any(), chain=AcceptChain())),
            '<Link "if any then LinkAction.defer" accept>')

    def test_link_repr_chain_and_function(self):
        def function():
            pass
        self.assertEqual(
            repr(Link(Any(), chain=AcceptChain(), function=function)),
            '<Link "if any then LinkAction.defer" accept function()>')

    def test_link_repr_chain_all(self):
        def function():
            pass
        self.assertEqual(
            repr(Link(Any(), LinkAction.stop, AcceptChain(), function)),
            '<Link "if any then LinkAction.stop" accept function()>')

    def test_flush(self):
        # Test that we can flush the links of a chain.
        chain = Chain('test', 'just a testing chain')
        chain.append_link(Link(Any()))
        # Iterate over the links of the chain to prove there are some.
        count = sum(1 for link in chain.get_iterator())
        self.assertEqual(count, 1)
        # Flush the chain; then there will be no links.
        chain.flush()
        count = sum(1 for link in chain.get_iterator())
        self.assertEqual(count, 0)


class TestTerminalChainBase(unittest.TestCase):
    layer = ConfigLayer

    def test_terminal_chain_iterator(self):
        chain = SimpleChain()
        self.assertEqual([link.action for link in chain],
                         [LinkAction.run, LinkAction.stop])
