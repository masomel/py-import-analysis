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

"""The header-matching chain."""

import re
import logging

from email.header import Header
from itertools import count
from mailman.chains.base import Chain, Link
from mailman.config import config
from mailman.core.i18n import _
from mailman.interfaces.chain import LinkAction
from mailman.interfaces.rules import IRule
from public import public
from zope.interface import implementer


log = logging.getLogger('mailman.error')
_RULE_COUNTER = count(1)


def _make_rule_name(suffix):
    # suffix may be None, since it comes from the 'name' parameter given in
    # the HeaderMatchRule constructor.
    if suffix is None:
        suffix = '{0:02}'.format(next(_RULE_COUNTER))
    return 'header-match-{}'.format(suffix)


def make_link(header, pattern, chain=None, suffix=None):
    """Create a Link object.

    The link action is to defer by default, since at the end of all the
    header checks, we'll jump to the chain defined in the configuration
    file, should any of them have matched.  However, it is possible to
    create a link which jumps to a specific chain.

    :param header: The email header name to check, e.g. X-Spam.
    :type header: string
    :param pattern: A regular expression for matching the header value.
    :type pattern: string
    :param chain: When given, this is the name of the chain to jump to if the
        pattern matches the header.
    :type chain: string
    :param suffix: An optional name suffix for the rule.
    :type suffix: string
    :return: The link representing this rule check.
    :rtype: `ILink`
    """
    rule_name = _make_rule_name(suffix)
    if rule_name in config.rules:
        rule = config.rules[rule_name]
    else:
        rule = HeaderMatchRule(header, pattern, suffix)
    if chain is None:
        return Link(rule)
    return Link(rule, LinkAction.jump, chain)


@implementer(IRule)
class HeaderMatchRule:
    """Header matching rule used by header-match chain."""

    def __init__(self, header, pattern, suffix=None):
        self.header = header
        self.pattern = pattern
        self.name = _make_rule_name(suffix)
        self.description = '{}: {}'.format(header, pattern)
        # XXX I think we should do better here, somehow recording that a
        # particular header matched a particular pattern, but that gets ugly
        # with RFC 2822 headers.  It also doesn't match well with the rule
        # name concept.  For now, we just record the rather useless numeric
        # rule name.  I suppose we could do the better hit recording in the
        # check() method, and set self.record = False.
        self.record = True
        # Register this rule so that other parts of the system can query it.
        assert self.name not in config.rules, (
            'Duplicate HeaderMatchRule: {} [{}: {}]'.format(
                self.name, self.header, self.pattern))
        config.rules[self.name] = self

    def check(self, mlist, msg, msgdata):
        """See `IRule`."""
        # Collect all the headers in all subparts.
        headers = []
        for p in msg.walk():
            headers.extend(p.get_all(self.header, []))
        for value in headers:
            if isinstance(value, Header):
                value = value.encode()
            if re.search(self.pattern, value, re.IGNORECASE):
                return True
        return False


@public
class HeaderMatchChain(Chain):
    """Default header matching chain.

    This could be extended by header match rules in the database.
    """

    def __init__(self):
        super().__init__(
            'header-match', _('The built-in header matching chain'))
        # This chain will dynamically calculate the links from the
        # configuration file, the database, and any explicitly added header
        # checks (via the .extend() method).
        self._extended_links = []

    def extend(self, header, pattern):
        """Extend the existing header matches.

        :param header: The case-insensitive header field name.
        :param pattern: The pattern to match the header's value again.  The
            match is not anchored and is done case-insensitively.
        """
        self._extended_links.append(make_link(header, pattern))

    def flush(self):
        """See `IMutableChain`."""
        # Remove all dynamically created rules.  Use the keys so we can mutate
        # the dictionary inside the loop.
        for rule_name in list(config.rules):
            if rule_name.startswith('header-match-'):
                del config.rules[rule_name]
        self._extended_links = []

    def get_links(self, mlist, msg, msgdata):
        """See `IChain`."""
        # First return all the configuration file links.
        for index, line in enumerate(
                config.antispam.header_checks.splitlines()):
            if len(line.strip()) == 0:
                continue
            parts = line.split(':', 1)
            if len(parts) != 2:
                log.error('Configuration error: [antispam]header_checks '
                          'contains bogus line: {}'.format(line))
                continue
            rule_name = 'config-{}'.format(index)
            yield make_link(parts[0], parts[1].lstrip(), suffix=rule_name)
        # Then return all the explicitly added links.
        yield from self._extended_links
        # If any of the above rules matched, they will have deferred their
        # action until now, so jump to the chain defined in the configuration
        # file.  For security considerations, this takes precedence over
        # list-specific matches.
        yield Link('any', LinkAction.jump, config.antispam.jump_chain)
        # Then return all the list-specific header matches.
        for index, entry in enumerate(mlist.header_matches):
            # Jump to the default antispam chain if the entry chain is None.
            chain = (config.antispam.jump_chain
                     if entry.chain is None
                     else entry.chain)
            rule_name = '{}-{}'.format(mlist.list_id, index)
            yield make_link(entry.header, entry.pattern, chain, rule_name)
