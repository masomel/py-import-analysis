# Copyright (C) 2011-2017 by the Free Software Foundation, Inc.
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

"""Testing app.bounces functions."""

import os
import uuid
import shutil
import tempfile
import unittest

from mailman.app.bounces import (
    ProbeVERP, StandardVERP, bounce_message, maybe_forward, send_probe)
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.interfaces.bounce import UnrecognizedBounceDisposition
from mailman.interfaces.languages import ILanguageManager
from mailman.interfaces.member import MemberRole
from mailman.interfaces.pending import IPendings
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import (
    LogFileMark, get_queue_messages, specialized_message_from_string as mfs,
    subscribe)
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestVERP(unittest.TestCase):
    """Test header VERP detection."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._verper = StandardVERP()

    def test_no_verp(self):
        # The empty set is returned when there is no VERP headers.
        msg = mfs("""\
From: postmaster@example.com
To: mailman-bounces@example.com

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg), set())

    def test_verp_in_to(self):
        # A VERP address is found in the To header.
        msg = mfs("""\
From: postmaster@example.com
To: test-bounces+anne=example.org@example.com

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg),
                         set(['anne@example.org']))

    def test_verp_in_delivered_to(self):
        # A VERP address is found in the Delivered-To header.
        msg = mfs("""\
From: postmaster@example.com
Delivered-To: test-bounces+anne=example.org@example.com

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg),
                         set(['anne@example.org']))

    def test_verp_in_envelope_to(self):
        # A VERP address is found in the Envelope-To header.
        msg = mfs("""\
From: postmaster@example.com
Envelope-To: test-bounces+anne=example.org@example.com

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg),
                         set(['anne@example.org']))

    def test_verp_in_apparently_to(self):
        # A VERP address is found in the Apparently-To header.
        msg = mfs("""\
From: postmaster@example.com
Apparently-To: test-bounces+anne=example.org@example.com

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg),
                         set(['anne@example.org']))

    def test_verp_with_empty_header(self):
        # A VERP address is found, but there's an empty header.
        msg = mfs("""\
From: postmaster@example.com
To: test-bounces+anne=example.org@example.com
To:

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg),
                         set(['anne@example.org']))

    def test_no_verp_with_empty_header(self):
        # There's an empty header, and no VERP address is found.
        msg = mfs("""\
From: postmaster@example.com
To:

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg), set())

    def test_verp_with_non_match(self):
        # A VERP address is found, but a header had a non-matching pattern.
        msg = mfs("""\
From: postmaster@example.com
To: test-bounces+anne=example.org@example.com
To: test-bounces@example.com

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg),
                         set(['anne@example.org']))

    def test_no_verp_with_non_match(self):
        # No VERP address is found, and a header had a non-matching pattern.
        msg = mfs("""\
From: postmaster@example.com
To: test-bounces@example.com

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg), set())

    def test_multiple_verps(self):
        # More than one VERP address was found in the same header.
        msg = mfs("""\
From: postmaster@example.com
To: test-bounces+anne=example.org@example.com
To: test-bounces+anne=example.org@example.com

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg),
                         set(['anne@example.org']))

    def test_multiple_verps_different_values(self):
        # More than one VERP address was found in the same header with
        # different values.
        msg = mfs("""\
From: postmaster@example.com
To: test-bounces+anne=example.org@example.com
To: test-bounces+bart=example.org@example.com

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg),
                         set(['anne@example.org', 'bart@example.org']))

    def test_multiple_verps_different_values_different_headers(self):
        # More than one VERP address was found in different headers with
        # different values.
        msg = mfs("""\
From: postmaster@example.com
To: test-bounces+anne=example.org@example.com
Apparently-To: test-bounces+bart=example.org@example.com

""")
        self.assertEqual(self._verper.get_verp(self._mlist, msg),
                         set(['anne@example.org', 'bart@example.org']))


class TestSendProbe(unittest.TestCase):
    """Test sending of the probe message."""

    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._mlist.send_welcome_message = False
        self._member = subscribe(self._mlist, 'Anne', email='anne@example.com')
        self._msg = mfs("""\
From: bouncer@example.com
To: anne@example.com
Subject: You bounced
Message-ID: <first>

""")

    def test_token(self):
        # Show that send_probe() returns a proper token, and that the token
        # corresponds to a record in the pending database.
        token = send_probe(self._member, self._msg)
        pendable = getUtility(IPendings).confirm(token)
        self.assertEqual(len(pendable.items()), 3)
        self.assertEqual(set(pendable.keys()),
                         set(['member_id', 'message_id', 'type']))
        # member_ids are pended as unicodes.
        self.assertEqual(uuid.UUID(hex=pendable['member_id']),
                         self._member.member_id)
        self.assertEqual(pendable['message_id'], '<first>')

    def test_probe_is_multipart(self):
        # The probe is a multipart/mixed with two subparts.
        send_probe(self._member, self._msg)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message.get_content_type(), 'multipart/mixed')
        self.assertTrue(message.is_multipart())
        self.assertEqual(len(message.get_payload()), 2)

    def test_probe_sends_one_message(self):
        # send_probe() places one message in the virgin queue.  We start out
        # with no messages in the queue.
        get_queue_messages('virgin', expected_count=0)
        send_probe(self._member, self._msg)
        get_queue_messages('virgin', expected_count=1)

    def test_probe_contains_original(self):
        # Show that send_probe() places a properly formatted message in the
        # virgin queue.
        send_probe(self._member, self._msg)
        items = get_queue_messages('virgin', expected_count=1)
        rfc822 = items[0].msg.get_payload(1)
        self.assertEqual(rfc822.get_content_type(), 'message/rfc822')
        self.assertTrue(rfc822.is_multipart())
        self.assertEqual(len(rfc822.get_payload()), 1)
        self.assertEqual(rfc822.get_payload(0).as_string(),
                         self._msg.as_string())

    def test_notice(self):
        # Test that the notice in the first subpart is correct.
        send_probe(self._member, self._msg)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        notice = message.get_payload(0)
        self.assertEqual(notice.get_content_type(), 'text/plain')
        # The interesting bits are the parts that have been interpolated into
        # the message.  For now the best we can do is know that the
        # interpolation values appear in the message.
        self.assertMultiLineEqual(notice.get_payload(), """\
This is a probe message.  You can ignore this message.

The test@example.com mailing list has received a number of bounces
from you, indicating that there may be a problem delivering messages
to anne@example.com.  A sample is attached below.  Please examine this
message to make sure there are no problems with your email address.
You may want to check with your mail administrator for more help.

You don't need to do anything to remain an enabled member of the
mailing list.

If you have any questions or problems, you can contact the mailing
list owner at

    test-owner@example.com
""")

    def test_headers(self):
        # Check the headers of the outer message.
        token = send_probe(self._member, self._msg)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        self.assertEqual(message['from'],
                         'test-bounces+{0}@example.com'.format(token))
        self.assertEqual(message['to'], 'anne@example.com')
        self.assertEqual(message['subject'], 'Test mailing list probe message')

    def test_no_precedence_header(self):
        # Probe messages should not have a Precedence header (LP: #808821).
        send_probe(self._member, self._msg)
        items = get_queue_messages('virgin', expected_count=1)
        self.assertIsNone(items[0].msg['precedence'])


class TestSendProbeNonEnglish(unittest.TestCase):
    """Test sending of the probe message to a non-English speaker."""

    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._member = subscribe(self._mlist, 'Anne', email='anne@example.com')
        self._msg = mfs("""\
From: bouncer@example.com
To: anne@example.com
Subject: You bounced
Message-ID: <first>

""")
        # Set up the translation context.
        self._var_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._var_dir)
        xx_template_path = os.path.join(
            self._var_dir, 'templates', 'site', 'xx',
            'list:user:notice:probe.txt')
        os.makedirs(os.path.dirname(xx_template_path))
        config.push('xx template dir', """\
        [paths.testing]
        var_dir: {}
        """.format(self._var_dir))
        self.addCleanup(config.pop, 'xx template dir')
        language_manager = getUtility(ILanguageManager)
        language_manager.add('xx', 'utf-8', 'Freedonia')
        self._member.preferences.preferred_language = 'xx'
        with open(xx_template_path, 'w') as fp:
            print("""\
blah blah blah
$listname
$address
$owneraddr
""", file=fp)

    def test_subject_with_member_nonenglish(self):
        # Test that members with non-English preferred language get a Subject
        # header in the expected language.
        send_probe(self._member, self._msg)
        items = get_queue_messages('virgin', expected_count=1)
        self.assertEqual(
            items[0].msg['subject'].encode(),
            '=?utf-8?q?ailing-may_ist-lay_Test_obe-pray_essage-may?=')

    def test_probe_notice_with_member_nonenglish(self):
        # Test that a member with non-English preferred language gets the
        # probe message in their language.
        send_probe(self._member, self._msg)
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        notice = message.get_payload(0).get_payload()
        self.assertMultiLineEqual(notice, """\
blah blah blah test@example.com anne@example.com
test-owner@example.com

""")


class TestProbe(unittest.TestCase):
    """Test VERP probe parsing."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._mlist.send_welcome_message = False
        self._member = subscribe(self._mlist, 'Anne', email='anne@example.com')
        self._msg = mfs("""\
From: bouncer@example.com
To: anne@example.com
Subject: You bounced
Message-ID: <first>

""")

    def test_get_addresses(self):
        # Be able to extract the probed address from the pending database
        # based on the token in a probe bounce.
        token = send_probe(self._member, self._msg)
        # Simulate a bounce of the message in the virgin queue.
        items = get_queue_messages('virgin', expected_count=1)
        message = items[0].msg
        bounce = mfs("""\
To: {0}
From: mail-daemon@example.com

""".format(message['From']))
        addresses = ProbeVERP().get_verp(self._mlist, bounce)
        self.assertEqual(addresses, set(['anne@example.com']))
        # The pendable is no longer in the database.
        self.assertIsNone(getUtility(IPendings).confirm(token))


class TestMaybeForward(unittest.TestCase):
    """Test forwarding of unrecognized bounces."""

    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        config.push('test config', """
        [mailman]
        site_owner: postmaster@example.com
        """)
        self.addCleanup(config.pop, 'test config')
        self._mlist = create_list('test@example.com')
        self._mlist.send_welcome_message = False
        self._msg = mfs("""\
From: bouncer@example.com
To: test-bounces@example.com
Subject: You bounced
Message-ID: <first>

""")

    def test_maybe_forward_discard(self):
        # When forward_unrecognized_bounces_to is set to discard, no bounce
        # messages are forwarded.
        self._mlist.forward_unrecognized_bounces_to = (
            UnrecognizedBounceDisposition.discard)
        # The only artifact of this call is a log file entry.
        mark = LogFileMark('mailman.bounce')
        maybe_forward(self._mlist, self._msg)
        get_queue_messages('virgin', expected_count=0)
        line = mark.readline()
        self.assertEqual(
            line[-40:-1],
            'Discarding unrecognized bounce: <first>')

    def test_maybe_forward_list_owner(self):
        # Set up some owner and moderator addresses.
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_address('anne@example.com')
        bart = user_manager.create_address('bart@example.com')
        cris = user_manager.create_address('cris@example.com')
        dave = user_manager.create_address('dave@example.com')
        # Regular members.
        elle = user_manager.create_address('elle@example.com')
        fred = user_manager.create_address('fred@example.com')
        self._mlist.subscribe(anne, MemberRole.owner)
        self._mlist.subscribe(bart, MemberRole.owner)
        self._mlist.subscribe(cris, MemberRole.moderator)
        self._mlist.subscribe(dave, MemberRole.moderator)
        self._mlist.subscribe(elle, MemberRole.member)
        self._mlist.subscribe(fred, MemberRole.member)
        # When forward_unrecognized_bounces_to is set to owners, the
        # bounce is forwarded to the list owners and moderators.
        self._mlist.forward_unrecognized_bounces_to = (
            UnrecognizedBounceDisposition.administrators)
        maybe_forward(self._mlist, self._msg)
        items = get_queue_messages('virgin', expected_count=1)
        msg = items[0].msg
        self.assertEqual(msg['subject'], 'Uncaught bounce notification')
        self.assertEqual(msg['from'], 'postmaster@example.com')
        self.assertEqual(msg['to'], 'test-owner@example.com')
        # The first attachment is a notification message with a url.
        payload = msg.get_payload(0)
        self.assertEqual(payload.get_content_type(), 'text/plain')
        body = payload.get_payload()
        self.assertMultiLineEqual(body, """\
The attached message was received as a bounce, but either the bounce format
was not recognized, or no member addresses could be extracted from it.  This
mailing list has been configured to send all unrecognized bounce messages to
the list administrator(s).
""")
        # The second attachment should be a message/rfc822 containing the
        # original bounce message.
        payload = msg.get_payload(1)
        self.assertEqual(payload.get_content_type(), 'message/rfc822')
        bounce = payload.get_payload(0)
        self.assertEqual(bounce.as_string(), self._msg.as_string())
        # All of the owners and moderators, but none of the members, should be
        # recipients of this message.
        self.assertEqual(items[0].msgdata['recipients'],
                         set(['anne@example.com', 'bart@example.com',
                              'cris@example.com', 'dave@example.com']))

    def test_maybe_forward_site_owner(self):
        # Set up some owner and moderator addresses.
        user_manager = getUtility(IUserManager)
        anne = user_manager.create_address('anne@example.com')
        bart = user_manager.create_address('bart@example.com')
        cris = user_manager.create_address('cris@example.com')
        dave = user_manager.create_address('dave@example.com')
        # Regular members.
        elle = user_manager.create_address('elle@example.com')
        fred = user_manager.create_address('fred@example.com')
        self._mlist.subscribe(anne, MemberRole.owner)
        self._mlist.subscribe(bart, MemberRole.owner)
        self._mlist.subscribe(cris, MemberRole.moderator)
        self._mlist.subscribe(dave, MemberRole.moderator)
        self._mlist.subscribe(elle, MemberRole.member)
        self._mlist.subscribe(fred, MemberRole.member)
        # When forward_unrecognized_bounces_to is set to owners, the
        # bounce is forwarded to the list owners and moderators.
        self._mlist.forward_unrecognized_bounces_to = (
            UnrecognizedBounceDisposition.site_owner)
        maybe_forward(self._mlist, self._msg)
        items = get_queue_messages('virgin', expected_count=1)
        msg = items[0].msg
        self.assertEqual(msg['subject'], 'Uncaught bounce notification')
        self.assertEqual(msg['from'], 'postmaster@example.com')
        self.assertEqual(msg['to'], 'postmaster@example.com')
        # The first attachment is a notification message with a url.
        payload = msg.get_payload(0)
        self.assertEqual(payload.get_content_type(), 'text/plain')
        body = payload.get_payload()
        self.assertMultiLineEqual(body, """\
The attached message was received as a bounce, but either the bounce format
was not recognized, or no member addresses could be extracted from it.  This
mailing list has been configured to send all unrecognized bounce messages to
the list administrator(s).
""")
        # The second attachment should be a message/rfc822 containing the
        # original bounce message.
        payload = msg.get_payload(1)
        self.assertEqual(payload.get_content_type(), 'message/rfc822')
        bounce = payload.get_payload(0)
        self.assertEqual(bounce.as_string(), self._msg.as_string())
        # All of the owners and moderators, but none of the members, should be
        # recipients of this message.
        self.assertEqual(items[0].msgdata['recipients'],
                         set(['postmaster@example.com']))


class TestBounceMessage(unittest.TestCase):
    """Test the `mailman.app.bounces.bounce_message()` function."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('test@example.com')
        self._msg = mfs("""\
From: anne@example.com
To: test@example.com
Subject: Ignore

""")

    def test_no_sender(self):
        # The message won't be bounced if it has no discernible sender.
        del self._msg['from']
        bounce_message(self._mlist, self._msg)
        # Nothing in the virgin queue means nothing's been bounced.
        get_queue_messages('virgin', expected_count=0)
