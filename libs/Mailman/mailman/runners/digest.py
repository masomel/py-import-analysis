# Copyright (C) 2009-2017 by the Free Software Foundation, Inc.
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

"""Digest runner."""

import os
import re
import logging

from copy import deepcopy
from email.header import Header
from email.mime.message import MIMEMessage
from email.mime.text import MIMEText
from email.utils import formatdate, getaddresses, make_msgid
from io import StringIO
from mailman.config import config
from mailman.core.i18n import _
from mailman.core.runner import Runner
from mailman.email.message import Message, MultipartDigestMessage
from mailman.handlers.decorate import decorate
from mailman.interfaces.member import DeliveryMode, DeliveryStatus
from mailman.interfaces.template import ITemplateLoader
from mailman.utilities.mailbox import Mailbox
from mailman.utilities.string import expand, oneline, wrap
from public import public
from zope.component import getUtility


log = logging.getLogger('mailman.error')


class Digester:
    """Base digester class."""

    def __init__(self, mlist, volume, digest_number):
        self._mlist = mlist
        self._charset = mlist.preferred_language.charset
        # This will be used in the Subject, so use $-strings.
        self._digest_id = _(
            '$mlist.display_name Digest, Vol $volume, Issue $digest_number')
        self._subject = Header(self._digest_id,
                               self._charset,
                               header_name='Subject')
        self._message = self._make_message()
        self._digest_part = self._make_digest_part()
        self._message['From'] = mlist.request_address
        self._message['Subject'] = self._subject
        self._message['To'] = mlist.posting_address
        self._message['Reply-To'] = mlist.posting_address
        self._message['Date'] = formatdate(localtime=True)
        self._message['Message-ID'] = make_msgid()
        # In the rfc1153 digest, the masthead contains the digest boilerplate
        # plus any digest header.  In the MIME digests, the masthead and
        # digest header are separate MIME subobjects.  In either case, it's
        # the first thing in the digest, and we can calculate it now, so go
        # ahead and add it now.
        template = getUtility(ITemplateLoader).get(
            'list:member:digest:masthead', mlist)
        self._masthead = wrap(expand(template, mlist, dict(
            # For backward compatibility.
            got_list_email=mlist.posting_address,
            got_request_email=mlist.request_address,
            got_owner_email=mlist.owner_address,
            )))
        # Set things up for the table of contents.
        self._header = decorate('list:member:digest:header', mlist)
        self._toc = StringIO()
        print(_("Today's Topics:\n"), file=self._toc)

    def add_to_toc(self, msg, count):
        """Add a message to the table of contents."""
        subject = msg.get('subject', _('(no subject)'))
        subject = oneline(subject, in_unicode=True)
        # Don't include the redundant subject prefix in the toc
        mo = re.match('(re:? *)?({0})'.format(
            re.escape(self._mlist.subject_prefix)),
                      subject, re.IGNORECASE)
        if mo:
            subject = subject[:mo.start(2)] + subject[mo.end(2):]
        # Take only the first author we find.
        username = ''
        addresses = getaddresses(
            [oneline(msg.get('from', ''), in_unicode=True)])
        if addresses:
            username = addresses[0][0]
            if not username:
                username = addresses[0][1]
        if username:
            username = ' ({})'.format(username)
        lines = wrap('{:2}. {}'. format(count, subject), 65).split('\n')
        # See if the user's name can fit on the last line
        if len(lines[-1]) + len(username) > 70:
            lines.append(username)
        else:
            lines[-1] += username
        # Add this subject to the accumulating topics
        first = True
        for line in lines:
            if first:
                print(' ', line, file=self._toc)
                first = False
            else:
                print('     ', line.lstrip(), file=self._toc)

    def add_message(self, msg, count):
        """Add the message to the digest."""
        # We do not want all the headers of the original message to leak
        # through in the digest messages.
        keepers = {}
        for header in self._keepers:
            keepers[header] = msg.get_all(header, [])
        # Remove all the unkempt <wink> headers.  Use .keys() to allow for
        # destructive iteration...
        for header in msg.keys():
            del msg[header]
        # ... and add them in the designated order.
        for header in self._keepers:
            for value in keepers[header]:
                msg[header] = value
        # Add some useful extra stuff.
        msg['Message'] = count.decode('utf-8')


class MIMEDigester(Digester):
    """A MIME digester."""

    def __init__(self, mlist, volume, digest_number):
        super().__init__(mlist, volume, digest_number)
        masthead = MIMEText(self._masthead.encode(self._charset),
                            _charset=self._charset)
        masthead['Content-Description'] = self._subject
        self._message.attach(masthead)
        # Add the optional digest header.
        if len(self._header) > 0:
            header = MIMEText(self._header.encode(self._charset),
                              _charset=self._charset)
            header['Content-Description'] = _('Digest Header')
            self._message.attach(header)
        # Calculate the set of headers we're to keep in the MIME digest.
        self._keepers = set(config.digests.mime_digest_keep_headers.split())

    def _make_message(self):
        return MultipartDigestMessage('mixed')

    def _make_digest_part(self):
        return MultipartDigestMessage('digest')

    def add_toc(self, count):
        """Add the table of contents."""
        toc_text = self._toc.getvalue()
        try:
            toc_part = MIMEText(toc_text.encode(self._charset),
                                _charset=self._charset)
        except UnicodeError:
            toc_part = MIMEText(toc_text.encode('utf-8'), _charset='utf-8')
        toc_part['Content-Description'] = _(
            "Today's Topics ($count messages)")
        self._message.attach(toc_part)

    def add_message(self, msg, count):
        """Add the message to the digest."""
        # Make a copy of the message object, since the RFC 1153 processing
        # scrubs out attachments.
        self._digest_part.attach(MIMEMessage(deepcopy(msg)))

    def finish(self):
        """Finish up the digest, producing the email-ready copy."""
        self._message.attach(self._digest_part)
        footer_text = decorate('list:member:digest:footer', self._mlist)
        if len(footer_text) > 0:
            footer = MIMEText(footer_text.encode(self._charset),
                              _charset=self._charset)
            footer['Content-Description'] = _('Digest Footer')
            self._message.attach(footer)
        # This stuff is outside the normal MIME goo, and it's what the old
        # MIME digester did.  No one seemed to complain, probably because you
        # won't see it in an MUA that can't display the raw message.  We've
        # never got complaints before, but if we do, just wax this.  It's
        # primarily included for (marginally useful) backwards compatibility.
        self._message.postamble = _('End of ') + self._digest_id
        return self._message


class RFC1153Digester(Digester):
    """A digester of the format specified by RFC 1153."""

    def __init__(self, mlist, volume, digest_number):
        super().__init__(mlist, volume, digest_number)
        self._separator70 = '-' * 70
        self._separator30 = '-' * 30
        self._text = StringIO()
        print(self._masthead, file=self._text)
        print(file=self._text)
        # Add the optional digest header.
        if len(self._header) > 0:
            print(self._header, file=self._text)
            print(file=self._text)
        # Calculate the set of headers we're to keep in the RFC1153 digest.
        self._keepers = set(config.digests.plain_digest_keep_headers.split())

    def _make_message(self):
        return Message()

    def _make_digest_part(self):
        # Not actually used here but referenced in super().__init__().
        return self._message

    def add_toc(self, count):
        """Add the table of contents."""
        print(self._toc.getvalue(), file=self._text)
        print(file=self._text)
        print(self._separator70, file=self._text)
        print(file=self._text)

    def add_message(self, msg, count):
        """Add the message to the digest."""
        if count > 1:
            print(self._separator30, file=self._text)
            print(file=self._text)
        # Each message section contains a few headers.
        for header in config.digests.plain_digest_keep_headers.split():
            if header in msg:
                value = oneline(msg[header], in_unicode=True)
                value = wrap('{}: {}'.format(header, value))
                value = '\n\t'.join(value.split('\n'))
                print(value, file=self._text)
        print(file=self._text)
        # Add the payload.  If the decoded payload is empty, this may be a
        # multipart message.  In that case, just stringify it.
        payload = msg.get_payload(decode=True)
        if not payload:
            payload = msg.as_string().split('\n\n', 1)[1]
        if isinstance(payload, bytes):
            try:
                # Do the decoding inside the try/except so that if the charset
                # conversion fails, we'll just drop back to ascii.
                charset = msg.get_content_charset('us-ascii')
                payload = payload.decode(charset, 'replace')
            except (LookupError, TypeError):
                # Unknown or empty charset.
                payload = payload.decode('us-ascii', 'replace')
        print(payload, file=self._text)
        if not payload.endswith('\n'):
            print(file=self._text)

    def finish(self):
        """Finish up the digest, producing the email-ready copy."""
        footer_text = decorate('list:member:digest:footer', self._mlist)
        if len(footer_text) > 0:
            # MAS: There is no real place for the digest_footer in an RFC 1153
            # compliant digest, so add it as an additional message with
            # Subject: Digest Footer
            print(self._separator30, file=self._text)
            print(file=self._text)
            print('Subject: ' + _('Digest Footer'), file=self._text)
            print(file=self._text)
            print(footer_text, file=self._text)
            print(file=self._text)
            print(self._separator30, file=self._text)
            print(file=self._text)
        # Add the sign-off.
        sign_off = _('End of ') + self._digest_id
        print(sign_off, file=self._text)
        print('*' * len(sign_off), file=self._text)
        # If the digest message can't be encoded by the list character set,
        # fall back to utf-8.
        text = self._text.getvalue()
        try:
            self._message.set_payload(text.encode(self._charset),
                                      charset=self._charset)
        except UnicodeError:
            self._message.set_payload(text.encode('utf-8'), charset='utf-8')
        return self._message


@public
class DigestRunner(Runner):
    """The digest runner."""

    def _dispose(self, mlist, msg, msgdata):
        """See `IRunner`."""
        volume = msgdata['volume']
        digest_number = msgdata['digest_number']
        # Backslashes make me cry.
        code = mlist.preferred_language.code
        with Mailbox(msgdata['digest_path']) as mailbox, _.using(code):
            # Create the digesters.
            mime_digest = MIMEDigester(mlist, volume, digest_number)
            rfc1153_digest = RFC1153Digester(mlist, volume, digest_number)
            # Cruise through all the messages in the mailbox, first building
            # the table of contents and accumulating Subject: headers and
            # authors.  The question really is whether it's better from a1
            # performance and memory footprint to go through the mailbox once
            # and cache the messages in a list, or to cruise through the
            # mailbox twice.  We'll do the latter, but it's a complete guess.
            count = None
            for count, (key, message) in enumerate(mailbox.iteritems(), 1):
                mime_digest.add_to_toc(message, count)
                rfc1153_digest.add_to_toc(message, count)
            assert count is not None, 'No digest messages?'
            # Add the table of contents.
            mime_digest.add_toc(count)
            rfc1153_digest.add_toc(count)
            # Cruise through the set of messages a second time, adding them to
            # the actual digest.
            for count, (key, message) in enumerate(mailbox.iteritems(), 1):
                mime_digest.add_message(message, count)
                rfc1153_digest.add_message(message, count)
            # Finish up the digests.
            mime = mime_digest.finish()
            rfc1153 = rfc1153_digest.finish()
        # Calculate the recipients lists
        mime_recipients = set()
        rfc1153_recipients = set()
        # When someone turns off digest delivery, they will get one last
        # digest to ensure that there will be no gaps in the messages they
        # receive.
        digest_members = set(mlist.digest_members.members)
        for member in digest_members:
            if member.delivery_status is not DeliveryStatus.enabled:
                continue
            # Send the digest to the case-preserved address of the digest
            # members.
            email_address = member.address.original_email
            if member.delivery_mode == DeliveryMode.plaintext_digests:
                rfc1153_recipients.add(email_address)
            # We currently treat summary_digests the same as mime_digests.
            elif member.delivery_mode in (DeliveryMode.mime_digests,
                                          DeliveryMode.summary_digests):
                mime_recipients.add(email_address)
            else:
                raise AssertionError(
                    'Digest member "{}" unexpected delivery mode: {}'.format(
                        email_address, member.delivery_mode))
        # Add also the folks who are receiving one last digest.
        for address, delivery_mode in mlist.last_digest_recipients:
            if delivery_mode == DeliveryMode.plaintext_digests:
                rfc1153_recipients.add(address.original_email)
            # We currently treat summary_digests the same as mime_digests.
            elif delivery_mode in (DeliveryMode.mime_digests,
                                   DeliveryMode.summary_digests):
                mime_recipients.add(address.original_email)
            else:
                raise AssertionError(
                    'OLD recipient "{}" unexpected delivery mode: {}'.format(
                        address, delivery_mode))
        # Send the digests to the virgin queue for final delivery.
        queue = config.switchboards['virgin']
        if len(mime_recipients) > 0:
            queue.enqueue(mime,
                          recipients=mime_recipients,
                          listid=mlist.list_id,
                          isdigest=True)
        if len(rfc1153_recipients) > 0:
            queue.enqueue(rfc1153,
                          recipients=rfc1153_recipients,
                          listid=mlist.list_id,
                          isdigest=True)
        # Remove the digest mbox. (GL #259)
        os.remove(msgdata['digest_path'])
