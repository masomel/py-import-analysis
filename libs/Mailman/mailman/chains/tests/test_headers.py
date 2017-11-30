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

"""Test the header chain."""

import unittest

from email import message_from_bytes
from mailman.app.lifecycle import create_list
from mailman.chains.headers import HeaderMatchRule, make_link
from mailman.config import config
from mailman.core.chains import process
from mailman.email.message import Message
from mailman.interfaces.chain import DiscardEvent, HoldEvent, LinkAction
from mailman.interfaces.mailinglist import IHeaderMatchList
from mailman.testing.helpers import (
    LogFileMark, configuration, event_subscribers,
    specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer


class TestHeaderChain(unittest.TestCase):
    """Test the header chain code."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')

    def test_make_link(self):
        # Test that make_link() with no given chain creates a Link with a
        # deferred link action.
        link = make_link('Subject', '[tT]esting')
        self.assertEqual(link.rule.header, 'Subject')
        self.assertEqual(link.rule.pattern, '[tT]esting')
        self.assertEqual(link.action, LinkAction.defer)
        self.assertIsNone(link.chain)

    def test_make_link_with_chain(self):
        # Test that make_link() with a given chain creates a Link with a jump
        # action to the chain.
        link = make_link('Subject', '[tT]esting', 'accept')
        self.assertEqual(link.rule.header, 'Subject')
        self.assertEqual(link.rule.pattern, '[tT]esting')
        self.assertEqual(link.action, LinkAction.jump)
        self.assertEqual(link.chain, config.chains['accept'])

    @configuration('antispam', header_checks="""
    Foo: a+
    Bar: bb?
    """)
    def test_config_checks(self):
        # Test that the header-match chain has the header checks from the
        # configuration file.
        chain = config.chains['header-match']
        # The links are created dynamically; the rule names will all start
        # with the same prefix, but have a variable suffix.  The actions will
        # all be to jump to the named chain.  Do these checks now, while we
        # collect other useful information.
        post_checks = []
        saw_any_rule = False
        for link in chain.get_links(self._mlist, Message(), {}):
            if link.rule.name == 'any':
                saw_any_rule = True
                self.assertEqual(link.action, LinkAction.jump)
            elif saw_any_rule:
                raise AssertionError("'any' rule was not last")
            else:
                self.assertEqual(link.rule.name[:13], 'header-match-')
                self.assertEqual(link.action, LinkAction.defer)
                post_checks.append((link.rule.header, link.rule.pattern))
        self.assertListEqual(post_checks, [
            ('Foo', 'a+'),
            ('Bar', 'bb?'),
            ])

    @configuration('antispam', header_checks="""
    Foo: foo
    A-bad-line
    Bar: bar
    """)
    def test_bad_configuration_line(self):
        # Take a mark on the error log file.
        mark = LogFileMark('mailman.error')
        # A bad value in [antispam]header_checks should just get ignored, but
        # with an error message logged.
        chain = config.chains['header-match']
        # The links are created dynamically; the rule names will all start
        # with the same prefix, but have a variable suffix.  The actions will
        # all be to jump to the named chain.  Do these checks now, while we
        # collect other useful information.
        post_checks = []
        saw_any_rule = False
        for link in chain.get_links(self._mlist, Message(), {}):
            if link.rule.name == 'any':
                saw_any_rule = True
                self.assertEqual(link.action, LinkAction.jump)
            elif saw_any_rule:
                raise AssertionError("'any' rule was not last")
            else:
                self.assertEqual(link.rule.name[:13], 'header-match-')
                self.assertEqual(link.action, LinkAction.defer)
                post_checks.append((link.rule.header, link.rule.pattern))
        self.assertListEqual(post_checks, [
            ('Foo', 'foo'),
            ('Bar', 'bar'),
            ])
        # Check the error log.
        self.assertEqual(mark.readline()[-77:-1],
                         'Configuration error: [antispam]header_checks '
                         'contains bogus line: A-bad-line')

    def test_duplicate_header_match_rule(self):
        # 100% coverage: test an assertion in a corner case.
        #
        # Save the existing rules so they can be restored later.
        saved_rules = config.rules.copy()
        self.addCleanup(setattr, config, 'rules', saved_rules)
        HeaderMatchRule('x-spam-score', '*', suffix='100')
        self.assertRaises(AssertionError,
                          HeaderMatchRule, 'x-spam-score', '.*', suffix='100')

    def test_list_rule(self):
        # Test that the header-match chain has the header checks from the
        # mailing-list configuration.
        chain = config.chains['header-match']
        header_matches = IHeaderMatchList(self._mlist)
        header_matches.append('Foo', 'a+')
        links = [link for link in chain.get_links(self._mlist, Message(), {})
                 if link.rule.name != 'any']
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].action, LinkAction.jump)
        self.assertEqual(links[0].chain.name, config.antispam.jump_chain)
        self.assertEqual(links[0].rule.header, 'foo')
        self.assertEqual(links[0].rule.pattern, 'a+')
        self.assertTrue(links[0].rule.name.startswith(
            'header-match-test.example.com-'))

    def test_list_complex_rule(self):
        # Test that the mailing-list header-match complex rules are read
        # properly.
        chain = config.chains['header-match']
        header_matches = IHeaderMatchList(self._mlist)
        header_matches.append('Foo', 'a+', 'reject')
        header_matches.append('Bar', 'b+', 'discard')
        header_matches.append('Baz', 'z+', 'accept')
        links = [link for link in chain.get_links(self._mlist, Message(), {})
                 if link.rule.name != 'any']
        self.assertEqual(len(links), 3)
        self.assertEqual([
            (link.rule.header, link.rule.pattern, link.action, link.chain.name)
            for link in links
            ],
            [('foo', 'a+', LinkAction.jump, 'reject'),
             ('bar', 'b+', LinkAction.jump, 'discard'),
             ('baz', 'z+', LinkAction.jump, 'accept'),
            ])                                      # noqa: E124

    def test_header_in_subpart(self):
        # Test that headers in sub-parts are also matched.
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A message
Message-ID: <ant>
Foo: foo
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="================12345=="

--================12345==
Content-Type: text/plain; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

A message body.

--================12345==
Content-Type: application/junk
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

This is junk

--================12345==--
""")
        msgdata = {}
        header_matches = IHeaderMatchList(self._mlist)
        header_matches.append('Content-Type', 'application/junk', 'hold')
        # This event subscriber records the event that occurs when the message
        # is processed by the owner chain.
        events = []
        with event_subscribers(events.append):
            process(self._mlist, msg, msgdata, start_chain='header-match')
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertIsInstance(event, HoldEvent)
        self.assertEqual(event.chain, config.chains['hold'])

    def test_get_all_returns_non_string(self):
        # Test case where msg.get_all() returns header instance.
        msg = message_from_bytes(b"""\
From: anne@example.com
To: test@example.com
Subject: Bad \x96 subject
Message-ID: <ant>

body

""", Message)
        msgdata = {}
        header_matches = IHeaderMatchList(self._mlist)
        header_matches.append('Subject', 'Bad', 'hold')
        # This event subscriber records the event that occurs when the message
        # is processed by the owner chain.
        events = []
        with event_subscribers(events.append):
            process(self._mlist, msg, msgdata, start_chain='header-match')
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertIsInstance(event, HoldEvent)
        self.assertEqual(event.chain, config.chains['hold'])

    @configuration('antispam', header_checks="""
    Foo: foo
    """, jump_chain='hold')
    def test_priority_site_over_list(self):
        # Test that the site-wide checks take precedence over the list-specific
        # checks.
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A message
Message-ID: <ant>
Foo: foo
MIME-Version: 1.0

A message body.
""")
        msgdata = {}
        header_matches = IHeaderMatchList(self._mlist)
        header_matches.append('Foo', 'foo', 'accept')
        # This event subscriber records the event that occurs when the message
        # is processed by the owner chain.
        events = []
        with event_subscribers(events.append):
            process(self._mlist, msg, msgdata, start_chain='header-match')
        self.assertEqual(len(events), 1)
        event = events[0]
        # Site-wide wants to hold the message, the list wants to accept it.
        self.assertIsInstance(event, HoldEvent)
        self.assertEqual(event.chain, config.chains['hold'])

    def test_no_action_defaults_to_site_wide_action(self):
        # If the list-specific header check matches, but there is no defined
        # action, the site-wide antispam action is used.
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A message
Message-ID: <ant>
Foo: foo
MIME-Version: 1.0

A message body.
""")
        header_matches = IHeaderMatchList(self._mlist)
        header_matches.append('Foo', 'foo')
        # This event subscriber records the event that occurs when the message
        # is processed by the owner chain, which holds its for approval.
        events = []
        def record_holds(event):                    # noqa: E301
            if not isinstance(event, HoldEvent):
                return
            events.append(event)
        with event_subscribers(record_holds):
            # Set the site-wide antispam action to hold the message.
            with configuration('antispam', header_checks="""
                Spam: [*]{3,}
                """, jump_chain='hold'):            # noqa: E125
                process(self._mlist, msg, {}, start_chain='header-match')
            self.assertEqual(len(events), 1)
            event = events[0]
            self.assertIsInstance(event, HoldEvent)
            self.assertEqual(event.chain, config.chains['hold'])
            self.assertEqual(event.mlist, self._mlist)
            self.assertEqual(event.msg, msg)
        events = []
        def record_discards(event):                 # noqa: E301
            if not isinstance(event, DiscardEvent):
                return
            events.append(event)
        with event_subscribers(record_discards):
            # Set the site-wide default to discard the message.
            msg.replace_header('Message-Id', '<bee>')
            with configuration('antispam', header_checks="""
                Spam: [*]{3,}
                """, jump_chain='discard'):         # noqa: E125
                process(self._mlist, msg, {}, start_chain='header-match')
            self.assertEqual(len(events), 1)
            event = events[0]
            self.assertIsInstance(event, DiscardEvent)
            self.assertEqual(event.chain, config.chains['discard'])
            self.assertEqual(event.mlist, self._mlist)
            self.assertEqual(event.msg, msg)

    @configuration('antispam', header_checks="""
    Header1: a+
    """, jump_chain='hold')
    def test_reuse_rules(self):
        # Test that existing header-match rules are used instead of creating
        # new ones.
        chain = config.chains['header-match']
        header_matches = IHeaderMatchList(self._mlist)
        header_matches.append('Header2', 'b+')
        header_matches.append('Header3', 'c+')
        def get_links():                          # noqa: E306
            return [
                link for link in chain.get_links(self._mlist, Message(), {})
                if link.rule.name != 'any'
                ]
        links_1 = get_links()
        self.assertEqual(len(links_1), 3)
        links_2 = get_links()
        # The link rules both have the same name...
        self.assertEqual(
            [l.rule.name for l in links_1],
            [l.rule.name for l in links_2],
            )
        # ...and are actually the identical objects.
        for link1, link2 in zip(links_1, links_2):
            self.assertIs(link1.rule, link2.rule)
