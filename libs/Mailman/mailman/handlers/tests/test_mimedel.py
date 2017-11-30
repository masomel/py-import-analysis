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

"""Test the mime_delete handler."""

import os
import sys
import email
import shutil
import tempfile
import unittest

from contextlib import ExitStack, contextmanager
from io import StringIO
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.handlers import mime_delete
from mailman.interfaces.action import FilterAction
from mailman.interfaces.member import MemberRole
from mailman.interfaces.pipeline import DiscardMessage, RejectMessage
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import (
    LogFileMark, configuration, get_queue_messages,
    specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from pkg_resources import resource_filename
from unittest.mock import patch
from zope.component import getUtility


@contextmanager
def dummy_script():
    with ExitStack() as resources:
        tempdir = tempfile.mkdtemp()
        resources.callback(shutil.rmtree, tempdir)
        filter_path = os.path.join(tempdir, 'filter.py')
        with open(filter_path, 'w', encoding='utf-8') as fp:
            print("""\
import sys
print('Converted text/html to text/plain')
print('Filename:', sys.argv[1])
""", file=fp)
        config.push('dummy script', """\
[mailman]
html_to_plain_text_command = {exe} {script} $filename
""".format(exe=sys.executable, script=filter_path))
        resources.callback(config.pop, 'dummy script')
        yield


class TestDispose(unittest.TestCase):
    """Test the mime_delete handler."""

    layer = ConfigLayer
    maxxDiff = None

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: A disposable message
Message-ID: <ant>

""")
        config.push('dispose', """
        [mailman]
        site_owner: noreply@example.com
        """)
        self.addCleanup(config.pop, 'dispose')

    def test_dispose_discard(self):
        self._mlist.filter_action = FilterAction.discard
        with self.assertRaises(DiscardMessage) as cm:
            mime_delete.dispose(self._mlist, self._msg, {}, 'discarding')
        self.assertEqual(cm.exception.message, 'discarding')
        # There should be no messages in the 'bad' queue.
        get_queue_messages('bad', expected_count=0)

    def test_dispose_bounce(self):
        self._mlist.filter_action = FilterAction.reject
        with self.assertRaises(RejectMessage) as cm:
            mime_delete.dispose(self._mlist, self._msg, {}, 'rejecting')
        self.assertEqual(cm.exception.message, 'rejecting')
        # There should be no messages in the 'bad' queue.
        get_queue_messages('bad', expected_count=0)

    def test_dispose_forward(self):
        # The disposed message gets forwarded to the list moderators.  So
        # first add some moderators.
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_address('anne@example.com')
        bart = user_manager.create_address('bart@example.com')
        self._mlist.subscribe(anne, MemberRole.moderator)
        self._mlist.subscribe(bart, MemberRole.moderator)
        # Now set the filter action and dispose the message.
        self._mlist.filter_action = FilterAction.forward
        with self.assertRaises(DiscardMessage) as cm:
            mime_delete.dispose(self._mlist, self._msg, {}, 'forwarding')
        self.assertEqual(cm.exception.message, 'forwarding')
        # There should now be a multipart message in the virgin queue destined
        # for the mailing list owners.
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message.get_content_type(), 'multipart/mixed')
        # Anne and Bart should be recipients of the message, but it will look
        # like the message is going to the list owners.
        self.assertEqual(message['to'], 'test-owner@example.com')
        self.assertEqual(message.recipients,
                         set(['anne@example.com', 'bart@example.com']))
        # The list owner should be the sender.
        self.assertEqual(message['from'], 'noreply@example.com')
        self.assertEqual(message['subject'],
                         'Content filter message notification')
        # The body of the first part provides the moderators some details.
        part0 = message.get_payload(0)
        self.assertEqual(part0.get_content_type(), 'text/plain')
        self.assertMultiLineEqual(part0.get_payload(), """\
The attached message matched the Test mailing list's content
filtering rules and was prevented from being forwarded on to the list
membership.  You are receiving the only remaining copy of the discarded
message.

""")
        # The second part is the container for the original message.
        part1 = message.get_payload(1)
        self.assertEqual(part1.get_content_type(), 'message/rfc822')
        # And the first part of *that* message will be the original message.
        original = part1.get_payload(0)
        self.assertEqual(original['subject'], 'A disposable message')
        self.assertEqual(original['message-id'], '<ant>')

    @configuration('mailman', filtered_messages_are_preservable='no')
    def test_dispose_non_preservable(self):
        # Two actions can happen here, depending on a site-wide setting.  If
        # the site owner has indicated that filtered messages cannot be
        # preserved, then this is the same as discarding them.
        self._mlist.filter_action = FilterAction.preserve
        with self.assertRaises(DiscardMessage) as cm:
            mime_delete.dispose(self._mlist, self._msg, {}, 'not preserved')
        self.assertEqual(cm.exception.message, 'not preserved')
        # There should be no messages in the 'bad' queue.
        get_queue_messages('bad', expected_count=0)

    @configuration('mailman', filtered_messages_are_preservable='yes')
    def test_dispose_preservable(self):
        # Two actions can happen here, depending on a site-wide setting.  If
        # the site owner has indicated that filtered messages can be
        # preserved, then this is similar to discarding the message except
        # that a copy is preserved in the 'bad' queue.
        self._mlist.filter_action = FilterAction.preserve
        with self.assertRaises(DiscardMessage) as cm:
            mime_delete.dispose(self._mlist, self._msg, {}, 'preserved')
        self.assertEqual(cm.exception.message, 'preserved')
        # There should be no messages in the 'bad' queue.
        items = get_queue_messages('bad', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['subject'], 'A disposable message')
        self.assertEqual(message['message-id'], '<ant>')

    def test_bad_action(self):
        # This should never happen, but what if it does?
        # FilterAction.accept, FilterAction.hold, and FilterAction.defer are
        # not valid.  They are treated as discard actions, but the problem is
        # also logged.
        for action in (FilterAction.accept,
                       FilterAction.hold,
                       FilterAction.defer):
            self._mlist.filter_action = action
            mark = LogFileMark('mailman.error')
            with self.assertRaises(DiscardMessage) as cm:
                mime_delete.dispose(self._mlist, self._msg, {}, 'bad action')
            self.assertEqual(cm.exception.message, 'bad action')
            line = mark.readline()[:-1]
            self.assertTrue(line.endswith(
                'test@example.com invalid FilterAction: {}.  '
                'Treating as discard'.format(action.name)))


class TestHTMLFilter(unittest.TestCase):
    """Test the conversion of HTML to plaintext."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._mlist.convert_html_to_plaintext = True
        self._mlist.filter_content = True

    def test_convert_html_to_plaintext(self):
        # Converting to plain text calls a command line script.
        msg = mfs("""\
From: aperson@example.com
Content-Type: text/html
MIME-Version: 1.0

<html><head></head>
<body></body></html>
""")
        process = config.handlers['mime-delete'].process
        with dummy_script():
            process(self._mlist, msg, {})
        self.assertEqual(msg.get_content_type(), 'text/plain')
        self.assertTrue(
            msg['x-content-filtered-by'].startswith('Mailman/MimeDel'))
        payload_lines = msg.get_payload().splitlines()
        self.assertEqual(payload_lines[0], 'Converted text/html to text/plain')


class TestMiscellaneous(unittest.TestCase):
    """Test various miscellaneous filtering actions."""

    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._mlist.collapse_alternatives = True
        self._mlist.filter_content = True
        self._mlist.filter_extensions = ['xlsx']

    def test_collapse_alternatives(self):
        email_file = resource_filename(
            'mailman.handlers.tests.data', 'collapse_alternatives.eml')
        with open(email_file) as fp:
            msg = email.message_from_file(fp)
        process = config.handlers['mime-delete'].process
        process(self._mlist, msg, {})
        structure = StringIO()
        email.iterators._structure(msg, fp=structure)
        self.assertEqual(structure.getvalue(), """\
multipart/signed
    multipart/mixed
        text/plain
        text/plain
    application/pgp-signature
""")

    def test_msg_rfc822(self):
        email_file = resource_filename(
            'mailman.handlers.tests.data', 'msg_rfc822.eml')
        email_file2 = resource_filename(
            'mailman.handlers.tests.data', 'msg_rfc822_out.eml')
        with open(email_file) as fp:
            msg = email.message_from_file(fp)
        process = config.handlers['mime-delete'].process
        with ExitStack() as resources:
            fp = resources.enter_context(open(email_file2))
            # Mock this so that the X-Content-Filtered-By header isn't
            # sensitive to Mailman version bumps.
            resources.enter_context(
                patch('mailman.handlers.mime_delete.VERSION', '123'))
            process(self._mlist, msg, {})
            self.assertEqual(msg.as_string(), fp.read())

    def test_mixed_case_ext_and_recast(self):
        msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: Testing mixed extension
Message-ID: <ant>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="AAAA"

--AAAA
Content-Type: text/plain; charset="utf-8"

Plain text

--AAAA
Content-Type: application/octet-stream; name="test.xlsX"
Content-Disposition: attachment; filename="test.xlsX"

spreadsheet

--AAAA--
""")
        process = config.handlers['mime-delete'].process
        process(self._mlist, msg, {})
        self.assertEqual(msg['content-type'], 'text/plain; charset="utf-8"')
        self.assertEqual(msg.get_payload(), """\
Plain text
""")
