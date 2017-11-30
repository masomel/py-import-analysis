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

"""Test the DMARC handler."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.app.membership import add_member
from mailman.handlers import dmarc
from mailman.interfaces.mailinglist import DMARCMitigateAction, ReplyToMunging
from mailman.interfaces.subscriptions import RequestRecord
from mailman.testing.helpers import specialized_message_from_string as mfs
from mailman.testing.layers import ConfigLayer


class TestDMARCMitigations(unittest.TestCase):
    """Test the dmarc handler."""

    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._mlist.anonymous_list = False
        self._mlist.dmarc_policy_mitigate_action = (
            DMARCMitigateAction.no_mitigation)
        self._mlist.dmarc_wrapped_message_text = ''
        self._mlist.dmarc_mitigate_unconditionally = False
        self._mlist.reply_goes_to_list = ReplyToMunging.no_munging
        # We can use the same message text for most tests.
        self._text = """\
From: anne@example.com
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Message-ID: <alpha@example.com>
Date: Fri, 1 Jan 2016 00:00:01 +0000
Another-Header: To test removal in wrapper
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="=====abc=="

--=====abc==
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Some things to say.
--=====abc==
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html><head></head><body>Some things to say.</body></html>
--=====abc==--
"""

    def test_default_no_change(self):
        msg = mfs(self._text)
        dmarc.process(self._mlist, msg, {})
        self.assertMultiLineEqual(msg.as_string(), self._text)

    def test_anonymous_no_change(self):
        self._mlist.anonymous_list = True
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
        msgdata = {'dmarc': True}
        msg = mfs(self._text)
        dmarc.process(self._mlist, msg, msgdata)
        self.assertMultiLineEqual(msg.as_string(), self._text)

    def test_no_mitigation_no_change_1(self):
        msg = mfs(self._text)
        self._mlist.dmarc_mitigate_unconditionally = True
        dmarc.process(self._mlist, msg, {})
        self.assertMultiLineEqual(msg.as_string(), self._text)

    def test_no_mitigation_no_change_2(self):
        msg = mfs(self._text)
        msgdata = {'dmarc': True}
        dmarc.process(self._mlist, msg, msgdata)
        self.assertMultiLineEqual(msg.as_string(), self._text)

    def test_action_reject_mitigate_unconditionally(self):
        msg = mfs(self._text)
        self._mlist.dmarc_mitigate_unconditionally = True
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.reject
        dmarc.process(self._mlist, msg, {})
        self.assertMultiLineEqual(msg.as_string(), self._text)

    def test_action_discard_mitigate_unconditionally(self):
        msg = mfs(self._text)
        self._mlist.dmarc_mitigate_unconditionally = True
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.discard
        dmarc.process(self._mlist, msg, {})
        self.assertMultiLineEqual(msg.as_string(), self._text)

    def test_action_munge_from(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
        msgdata = {'dmarc': True}
        msg = mfs(self._text)
        dmarc.process(self._mlist, msg, msgdata)
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Message-ID: <alpha@example.com>
Date: Fri, 1 Jan 2016 00:00:01 +0000
Another-Header: To test removal in wrapper
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="=====abc=="
From: anne--- via Ant <ant@example.com>
Reply-To: anne@example.com

--=====abc==
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Some things to say.
--=====abc==
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html><head></head><body>Some things to say.</body></html>
--=====abc==--
""")

    def test_action_munge_from_no_from(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
        msgdata = dict(
            dmarc=True,
            original_sender='anne@example.com',
            )
        msg = mfs(self._text)
        del msg['from']
        dmarc.process(self._mlist, msg, msgdata)
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Message-ID: <alpha@example.com>
Date: Fri, 1 Jan 2016 00:00:01 +0000
Another-Header: To test removal in wrapper
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="=====abc=="
From: anne--- via Ant <ant@example.com>
Reply-To: anne@example.com

--=====abc==
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Some things to say.
--=====abc==
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html><head></head><body>Some things to say.</body></html>
--=====abc==--
""")

    def test_action_munge_multiple_froms(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
        msgdata = dict(
            dmarc=True,
            original_sender='cate@example.com',
            )
        msg = mfs(self._text)
        # Put multiple addresses in the From: header.  The msgdata must
        # contain a key naming the "original sender" as determined by the
        # Message.sender attribute.
        del msg['from']
        msg['From'] = 'anne@example.com, bart@example.com'
        dmarc.process(self._mlist, msg, msgdata)
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Message-ID: <alpha@example.com>
Date: Fri, 1 Jan 2016 00:00:01 +0000
Another-Header: To test removal in wrapper
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="=====abc=="
From: cate--- via Ant <ant@example.com>
Reply-To: cate@example.com

--=====abc==
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Some things to say.
--=====abc==
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html><head></head><body>Some things to say.</body></html>
--=====abc==--
""")

    def test_action_munge_from_display_name_in_from(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
        msgdata = {'dmarc': True}
        msg = mfs(self._text)
        del msg['from']
        msg['From'] = 'Anne Person <anne@example.com>'
        dmarc.process(self._mlist, msg, msgdata)
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Message-ID: <alpha@example.com>
Date: Fri, 1 Jan 2016 00:00:01 +0000
Another-Header: To test removal in wrapper
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="=====abc=="
From: Anne Person via Ant <ant@example.com>
Reply-To: Anne Person <anne@example.com>

--=====abc==
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Some things to say.
--=====abc==
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html><head></head><body>Some things to say.</body></html>
--=====abc==--
""")

    def test_action_munge_from_display_name_in_list(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
        add_member(
            self._mlist,
            RequestRecord('anne@example.com', 'Anna Banana')
            )
        msgdata = {'dmarc': True}
        msg = mfs(self._text)
        dmarc.process(self._mlist, msg, msgdata)
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Message-ID: <alpha@example.com>
Date: Fri, 1 Jan 2016 00:00:01 +0000
Another-Header: To test removal in wrapper
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="=====abc=="
From: Anna Banana via Ant <ant@example.com>
Reply-To: anne@example.com

--=====abc==
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Some things to say.
--=====abc==
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html><head></head><body>Some things to say.</body></html>
--=====abc==--
""")

    def test_no_action_without_msgdata(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
        msg = mfs(self._text)
        dmarc.process(self._mlist, msg, {})
        self.assertMultiLineEqual(msg.as_string(), self._text)

    def test_unconditional_no_msgdata(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
        self._mlist.dmarc_mitigate_unconditionally = True
        msg = mfs(self._text)
        dmarc.process(self._mlist, msg, {})
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Message-ID: <alpha@example.com>
Date: Fri, 1 Jan 2016 00:00:01 +0000
Another-Header: To test removal in wrapper
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="=====abc=="
From: anne--- via Ant <ant@example.com>
Reply-To: anne@example.com

--=====abc==
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Some things to say.
--=====abc==
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html><head></head><body>Some things to say.</body></html>
--=====abc==--
""")

    def test_from_in_cc(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
        self._mlist.reply_goes_to_list = ReplyToMunging.point_to_list
        msgdata = {'dmarc': True}
        msg = mfs(self._text)
        dmarc.process(self._mlist, msg, msgdata)
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Message-ID: <alpha@example.com>
Date: Fri, 1 Jan 2016 00:00:01 +0000
Another-Header: To test removal in wrapper
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="=====abc=="
From: anne--- via Ant <ant@example.com>
Cc: anne@example.com

--=====abc==
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Some things to say.
--=====abc==
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html><head></head><body>Some things to say.</body></html>
--=====abc==--
""")

    def test_wrap_message_unconditionally(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.wrap_message
        self._mlist.dmarc_mitigate_unconditionally = True
        msg = mfs(self._text)
        dmarc.process(self._mlist, msg, {})
        # We can't predict the Message-ID in the wrapper so delete it, but
        # ensure we have one.
        self.assertIsNotNone(msg.get('message-id'))
        del msg['message-id']
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Date: Fri, 1 Jan 2016 00:00:01 +0000
MIME-Version: 1.0
From: anne--- via Ant <ant@example.com>
Reply-To: anne@example.com
Content-Type: message/rfc822
Content-Disposition: inline

""" + self._text)

    def test_wrap_message(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.wrap_message
        msgdata = {'dmarc': True}
        msg = mfs(self._text)
        dmarc.process(self._mlist, msg, msgdata)
        # We can't predict the Message-ID in the wrapper so delete it, but
        # ensure we have one.
        self.assertIsNotNone(msg.get('message-id'))
        del msg['message-id']
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Date: Fri, 1 Jan 2016 00:00:01 +0000
MIME-Version: 1.0
From: anne--- via Ant <ant@example.com>
Reply-To: anne@example.com
Content-Type: message/rfc822
Content-Disposition: inline

""" + self._text)

    def test_wrap_message_cc(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.wrap_message
        self._mlist.reply_goes_to_list = ReplyToMunging.point_to_list
        msgdata = {'dmarc': True}
        msg = mfs(self._text)
        dmarc.process(self._mlist, msg, msgdata)
        # We can't predict the Message-ID in the wrapper so delete it, but
        # ensure we have one.
        self.assertIsNotNone(msg.get('message-id'))
        del msg['message-id']
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Date: Fri, 1 Jan 2016 00:00:01 +0000
MIME-Version: 1.0
From: anne--- via Ant <ant@example.com>
Cc: anne@example.com
Content-Type: message/rfc822
Content-Disposition: inline

""" + self._text)

    def test_rfc2047_encoded_from(self):
        self._mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
        msgdata = {'dmarc': True}
        msg = mfs(self._text)
        del msg['from']
        msg['From'] = '=?iso-8859-1?Q?A_Pers=F3n?= <anne@example.com>'
        dmarc.process(self._mlist, msg, msgdata)
        self.assertMultiLineEqual(msg.as_string(), """\
To: ant@example.com
Subject: A subject
X-Mailman-Version: X.Y
Message-ID: <alpha@example.com>
Date: Fri, 1 Jan 2016 00:00:01 +0000
Another-Header: To test removal in wrapper
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="=====abc=="
From: =?utf-8?q?A_Pers=C3=B3n_via_Ant?= <ant@example.com>
Reply-To: =?iso-8859-1?Q?A_Pers=F3n?= <anne@example.com>

--=====abc==
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit

Some things to say.
--=====abc==
Content-Type: text/html; charset="us-ascii"
Content-Transfer-Encoding: 7bit

<html><head></head><body>Some things to say.</body></html>
--=====abc==--
""")
