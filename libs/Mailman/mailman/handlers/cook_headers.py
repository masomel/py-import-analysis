# Copyright (C) 1998-2017 by the Free Software Foundation, Inc.
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

"""Cook a message's headers."""

import logging

from email.header import Header
from email.utils import formataddr, getaddresses, parseaddr
from mailman.core.i18n import _
from mailman.interfaces.handler import IHandler
from mailman.interfaces.mailinglist import Personalization, ReplyToMunging
from mailman.version import VERSION
from public import public
from zope.interface import implementer


log = logging.getLogger('mailman.error')

COMMASPACE = ', '
MAXLINELEN = 78


@public
def uheader(mlist, s, header_name=None, continuation_ws='\t', maxlinelen=None):
    """Get the charset to encode the string in.

    Then search if there is any non-ascii character is in the string.  If
    there is and the charset is us-ascii then we use iso-8859-1 instead.  If
    the string is ascii only we use 'us-ascii' if another charset is
    specified.

    If the header contains a newline, truncate it (see GL#273).
    """
    charset = mlist.preferred_language.charset
    if '\n' in s:
        s = '{} [...]'.format(s.split('\n')[0])
        log.warning('Header {} contains a newline, truncating it.'.format(
            header_name, s))
    return Header(s, charset, maxlinelen, header_name, continuation_ws)


def process(mlist, msg, msgdata):
    """Process the headers of the message."""
    # Set the "X-Ack: no" header if noack flag is set.
    if msgdata.get('noack'):
        del msg['x-ack']
        msg['X-Ack'] = 'no'
    # Because we're going to modify various important headers in the email
    # message, we want to save some of the information in the msgdata
    # dictionary for later.  Specifically, the sender header will get waxed,
    # but we need it for the Acknowledge module later.
    msgdata['original_sender'] = msg.sender
    # VirginRunner sets _fasttrack for internally crafted messages.
    fasttrack = msgdata.get('_fasttrack')
    # Add Precedence: and other useful headers.  None of these are standard
    # and finding information on some of them are fairly difficult.  Some are
    # just common practice, and we'll add more here as they become necessary.
    # Good places to look are:
    #
    # http://www.dsv.su.se/~jpalme/ietf/jp-ietf-home.html
    # http://www.faqs.org/rfcs/rfc2076.html
    #
    # None of these headers are added if they already exist.  BAW: some
    # consider the advertising of this a security breach.  I.e. if there are
    # known exploits in a particular version of Mailman and we know a site is
    # using such an old version, they may be vulnerable.  It's too easy to
    # edit the code to add a configuration variable to handle this.
    if 'x-mailman-version' not in msg:
        msg['X-Mailman-Version'] = VERSION
    # We set "Precedence: list" because this is the recommendation from the
    # sendmail docs, the most authoritative source of this header's semantics.
    if 'precedence' not in msg:
        msg['Precedence'] = 'list'
    # Reply-To: munging.  Do not do this if the message is "fast tracked",
    # meaning it is internally crafted and delivered to a specific user.  BAW:
    # Yuck, I really hate this feature but I've caved under the sheer pressure
    # of the (very vocal) folks want it.  OTOH, RFC 2822 allows Reply-To: to
    # be a list of addresses, so instead of replacing the original, simply
    # augment it.  RFC 2822 allows max one Reply-To: header so collapse them
    # if we're adding a value, otherwise don't touch it.  (Should we collapse
    # in all cases?)
    if not fasttrack:
        # A convenience function, requires nested scopes.  pair is (name, addr)
        new = []
        d = {}
        def add(pair):                              # noqa: E306
            lcaddr = pair[1].lower()
            if lcaddr in d:
                return
            d[lcaddr] = pair
            new.append(pair)
        # List admin wants an explicit Reply-To: added
        if mlist.reply_goes_to_list is ReplyToMunging.explicit_header:
            add(parseaddr(mlist.reply_to_address))
        # If we're not first stripping existing Reply-To: then we need to add
        # the original Reply-To:'s to the list we're building up.  In both
        # cases we'll zap the existing field because RFC 2822 says max one is
        # allowed.
        if not mlist.first_strip_reply_to:
            orig = msg.get_all('reply-to', [])
            for pair in getaddresses(orig):
                add(pair)
        # Set Reply-To: header to point back to this list.  Add this last
        # because some folks think that some MUAs make it easier to delete
        # addresses from the right than from the left.
        if mlist.reply_goes_to_list is ReplyToMunging.point_to_list:
            i18ndesc = uheader(mlist, mlist.description, 'Reply-To')
            add((str(i18ndesc), mlist.posting_address))
        del msg['reply-to']
        # Don't put Reply-To: back if there's nothing to add!
        if new:
            # Preserve order
            msg['Reply-To'] = COMMASPACE.join(
                [formataddr(pair) for pair in new])
        # The To field normally contains the list posting address.  However
        # when messages are fully personalized, that header will get
        # overwritten with the address of the recipient.  We need to get the
        # posting address in one of the recipient headers or they won't be
        # able to reply back to the list.  It's possible the posting address
        # was munged into the Reply-To header, but if not, we'll add it to a
        # Cc header.  BAW: should we force it into a Reply-To header in the
        # above code?
        # Also skip Cc if this is an anonymous list as list posting address
        # is already in From and Reply-To in this case.
        if (mlist.personalize is Personalization.full
                and mlist.reply_goes_to_list is not               # noqa: W503
                    ReplyToMunging.point_to_list
                and not mlist.anonymous_list):                    # noqa: W503
            # Watch out for existing Cc headers, merge, and remove dups.  Note
            # that RFC 2822 says only zero or one Cc header is allowed.
            new = []
            d = {}
            for pair in getaddresses(msg.get_all('cc', [])):
                add(pair)
            i18ndesc = uheader(mlist, mlist.description, 'Cc')
            add((str(i18ndesc), mlist.posting_address))
            del msg['Cc']
            msg['Cc'] = COMMASPACE.join([formataddr(pair) for pair in new])


@public
@implementer(IHandler)
class CookHeaders:
    """Modify message headers."""

    name = 'cook-headers'
    description = _('Modify message headers.')

    def process(self, mlist, msg, msgdata):
        """See `IHandler`."""
        process(mlist, msg, msgdata)
