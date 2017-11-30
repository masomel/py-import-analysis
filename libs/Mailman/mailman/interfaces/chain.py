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

"""Interfaces describing the basics of chains and links."""

from enum import Enum
from public import public
from zope.interface import Attribute, Interface


@public
class ChainEvent:
    """Base class for chain notification events."""

    def __init__(self, mlist, msg, msgdata, chain):
        self.mlist = mlist
        self.msg = msg
        self.msgdata = msgdata
        self.chain = chain


@public
class AcceptEvent(ChainEvent):
    """A notification event signaling that a message is being accepted."""


@public
class AcceptOwnerEvent(ChainEvent):
    """An event signaling that a message is accepted to the -owner address."""


@public
class DiscardEvent(ChainEvent):
    """A notification event signaling that a message is being discarded."""


@public
class HoldEvent(ChainEvent):
    """A notification event signaling that a message is being held."""


@public
class RejectEvent(ChainEvent):
    """A notification event signaling that a message is being rejected."""


@public
class LinkAction(Enum):
    # Jump to another chain.
    jump = 0
    # Take a detour to another chain, returning to the original chain when
    # completed (if no other jump occurs).
    detour = 1
    # Stop processing all chains.
    stop = 2
    # Continue processing the next link in the chain.
    defer = 3
    # Run a function and continue processing.
    run = 4


@public
class IChainLink(Interface):
    """A link in the chain."""

    rule = Attribute('The rule to run for this link.')

    action = Attribute('The LinkAction to take if this rule matches.')

    chain = Attribute('The chain to jump or detour to.')

    function = Attribute(
        """The function to execute.

        The function takes three arguments and returns nothing.
        :param mlist: the IMailingList object
        :param msg: the message being processed
        :param msgdata: the message metadata dictionary
        """)


@public
class IChain(Interface):
    """A chain of rules."""

    name = Attribute('Chain name; must be unique.')
    description = Attribute('A brief description of the chain.')

    def get_links(mlist, msg, msgdata):
        """Get an `IChainIterator` for processing.

        :param mlist: The mailing list.
        :param msg: The message being processed.
        :param msgdata: The message metadata dictionary.
        :return: `IChainIterator`.
        """


@public
class IChainIterator(Interface):
    """An iterator over chain rules."""

    def __iter__():
        """Iterate over all the IChainLinks in this chain.

        :return: an IChainLink.
        """


@public
class IMutableChain(IChain):
    """Like `IChain` but can be mutated."""

    def append_link(link):
        """Add a new chain link to the end of this chain.

        :param link: The chain link to add.
        """

    def flush():
        """Delete all links in this chain."""
