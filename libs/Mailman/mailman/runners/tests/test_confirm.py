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

"""Test the `confirm` command."""

import unittest

from datetime import datetime
from email.iterators import body_line_iterator
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.database.transaction import transaction
from mailman.interfaces.subscriptions import ISubscriptionManager
from mailman.interfaces.usermanager import IUserManager
from mailman.runners.command import CommandRunner
from mailman.testing.helpers import (
    get_queue_messages, make_testable_runner,
    specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestConfirm(unittest.TestCase):
    """Test confirmations."""

    layer = ConfigLayer

    def setUp(self):
        self._commandq = config.switchboards['command']
        self._runner = make_testable_runner(CommandRunner, 'command')
        with transaction():
            # Register a subscription requiring confirmation.
            self._mlist = create_list('test@example.com')
            self._mlist.send_welcome_message = False
            anne = getUtility(IUserManager).create_address('anne@example.org')
            registrar = ISubscriptionManager(self._mlist)
            self._token, token_owner, member = registrar.register(anne)

    def test_confirm_with_re_prefix(self):
        subject = 'Re: confirm {}'.format(self._token)
        msg = mfs("""\
From: anne@example.org
To: test-confirm@example.com

""")
        msg['Subject'] = subject
        self._commandq.enqueue(msg, dict(listid='test.example.com'))
        self._runner.run()
        # Anne is now a confirmed member so her user record and email address
        # should exist in the database.
        manager = getUtility(IUserManager)
        user = manager.get_user('anne@example.org')
        address = list(user.addresses)[0]
        self.assertEqual(address.email, 'anne@example.org')
        self.assertEqual(address.verified_on, datetime(2005, 8, 1, 7, 49, 23))
        address = manager.get_address('anne@example.org')
        self.assertEqual(address.email, 'anne@example.org')

    def test_confirm_with_random_ascii_prefix(self):
        subject = '\x99AW: confirm {}'.format(self._token)
        msg = mfs("""\
From: anne@example.org
To: test-confirm@example.com

""")
        msg['Subject'] = subject
        self._commandq.enqueue(msg, dict(listid='test.example.com'))
        self._runner.run()
        # Anne is now a confirmed member so her user record and email address
        # should exist in the database.
        manager = getUtility(IUserManager)
        user = manager.get_user('anne@example.org')
        address = list(user.addresses)[0]
        self.assertEqual(address.email, 'anne@example.org')
        self.assertEqual(address.verified_on, datetime(2005, 8, 1, 7, 49, 23))
        address = manager.get_address('anne@example.org')
        self.assertEqual(address.email, 'anne@example.org')

    def test_confirm_with_utf8_body(self):
        # Clear out the virgin queue so that the test below only sees the
        # reply to the confirmation message.
        get_queue_messages('virgin')
        subject = 'Re: confirm {}'.format(self._token)
        to = 'test-confirm+{}@example.com'.format(self._token)
        msg = mfs("""\
From: Anne Person <anne@example.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Disposition: inline
Content-Transfer-Encoding: quoted-printable

* test-confirm+90bf6ef335d92cfbbe540a5c9ebfecb107a48e48@example.com <=
test-confirm+90bf6ef335d92cfbbe540a5c9ebfecb107a48e48@example.com>:
> Email Address Registration Confirmation
>=20
> Hello, this is the GNU Mailman server at example.com.
>=20
> We have received a registration request for the email address
>=20
>     anne@example.org
>=20
> Before you can start using GNU Mailman at this site, you must first con=
firm
> that this is your email address.  You can do this by replying to this m=
essage,
> keeping the Subject header intact.  Or you can visit this web page
>=20
>     http://example.com/confirm/90bf6ef335d92cfbbe540a5c9ebfecb107a48e48
>=20
> If you do not wish to register this email address simply disregard this
> message.  If you think you are being maliciously subscribed to the list=
, or
> have any other questions, you may contact
>=20
>     postmaster@example.com

--=20

Franziskanerstra=C3=9Fe
""")
        msg['Subject'] = subject
        msg['To'] = to
        self._commandq.enqueue(msg, dict(listid='test.example.com'))
        self._runner.run()
        # Anne is now a confirmed member so her user record and email address
        # should exist in the database.
        manager = getUtility(IUserManager)
        user = manager.get_user('anne@example.org')
        address = list(user.addresses)[0]
        self.assertEqual(address.email, 'anne@example.org')
        self.assertEqual(address.verified_on, datetime(2005, 8, 1, 7, 49, 23))
        address = manager.get_address('anne@example.org')
        self.assertEqual(address.email, 'anne@example.org')
        items = get_queue_messages('virgin', expected_count=1)
        self.assertEqual(items[0].msgdata['recipients'],
                         set(['anne@example.org']))

    def test_confirm_with_no_command_in_utf8_body(self):
        # Clear out the virgin queue so that the test below only sees the
        # reply to the confirmation message.
        get_queue_messages('virgin')
        subject = 'Re: confirm {}'.format(self._token)
        to = 'test-confirm+{}@example.com'.format(self._token)
        msg = mfs("""\
From: Anne Person <anne@example.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Disposition: inline
Content-Transfer-Encoding: quoted-printable

Franziskanerstra=C3=9Fe
""")
        msg['Subject'] = subject
        msg['To'] = to
        self._commandq.enqueue(msg, dict(listid='test.example.com'))
        self._runner.run()
        # Anne is now a confirmed member so her user record and email address
        # should exist in the database.
        manager = getUtility(IUserManager)
        user = manager.get_user('anne@example.org')
        address = list(user.addresses)[0]
        self.assertEqual(address.email, 'anne@example.org')
        self.assertEqual(address.verified_on, datetime(2005, 8, 1, 7, 49, 23))
        address = manager.get_address('anne@example.org')
        self.assertEqual(address.email, 'anne@example.org')
        items = get_queue_messages('virgin', expected_count=1)
        self.assertEqual(items[0].msgdata['recipients'],
                         set(['anne@example.org']))

    def test_double_confirmation(self):
        # 'confirm' in the Subject and in the To header should not try to
        # confirm the token twice.
        #
        # Clear out the virgin queue so that the test below only sees the
        # reply to the confirmation message.
        get_queue_messages('virgin')
        subject = 'Re: confirm {}'.format(self._token)
        to = 'test-confirm+{}@example.com'.format(self._token)
        msg = mfs("""\
From: Anne Person <anne@example.org>

""")
        msg['Subject'] = subject
        msg['To'] = to
        self._commandq.enqueue(msg, dict(listid='test.example.com',
                                         subaddress='confirm'))
        self._runner.run()
        # Anne is now a confirmed member so her user record and email address
        # should exist in the database.
        manager = getUtility(IUserManager)
        user = manager.get_user('anne@example.org')
        self.assertEqual(list(user.addresses)[0].email, 'anne@example.org')
        # Make sure that the confirmation was not attempted twice.
        items = get_queue_messages('virgin', expected_count=1)
        # Search the contents of the results message.  There should be just
        # one 'Confirmation email' line.
        confirmation_lines = []
        in_results = False
        for line in body_line_iterator(items[0].msg):
            line = line.strip()
            if in_results:
                if line.startswith('- Done'):
                    break
                if len(line) > 0:
                    confirmation_lines.append(line)
            if line.strip() == '- Results:':
                in_results = True
        self.assertEqual(len(confirmation_lines), 1)
        self.assertNotIn('did not match', confirmation_lines[0])

    def test_welcome_message_after_confirmation(self):
        # Confirmations with a welcome message set.
        self._mlist.send_welcome_message = True
        self._mlist.welcome_message_uri = 'mailman:///welcome.txt'
        # 'confirm' in the Subject and in the To header should not try to
        # confirm the token twice.
        #
        # Clear out the virgin queue so that the test below only sees the
        # reply to the confirmation message.
        get_queue_messages('virgin')
        subject = 'Re: confirm {}'.format(self._token)
        to = 'test-confirm+{}@example.com'.format(self._token)
        msg = mfs("""\
From: Anne Person <anne@example.org>

""")
        msg['Subject'] = subject
        msg['To'] = to
        self._commandq.enqueue(msg, dict(listid='test.example.com',
                                         subaddress='confirm'))
        self._runner.run()
        # Now there's a email command notification and a welcome message.  All
        # we care about for this test is the welcome message.
        items = get_queue_messages('virgin', sort_on='subject',
                                   expected_count=2)
        self.assertEqual(str(items[1].msg['subject']),
                         'Welcome to the "Test" mailing list')
