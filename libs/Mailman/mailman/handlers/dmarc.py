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

"""Do DMARC Munge From and Wrap Message actions.

This does the work of modifying the messages From: and Cc: or Reply-To: or
wrapping the message in an outer message with From: and Cc: or Reply-To:
as appropriate to avoid issues because of the original From: domain's DMARC
policy.  It does this either to selected messages flagged by the DMARC
moderation rule based on list settings and the original From: domain's DMARC
policy or to all messages based on list settings."""

import re
import copy
import logging

from email.header import Header, decode_header
from email.mime.message import MIMEMessage
from email.mime.text import MIMEText
from email.utils import formataddr, getaddresses, make_msgid
from mailman.core.i18n import _
from mailman.interfaces.handler import IHandler
from mailman.interfaces.mailinglist import DMARCMitigateAction, ReplyToMunging
from mailman.utilities.string import wrap
from public import public
from zope.interface import implementer


log = logging.getLogger('mailman.error')

COMMASPACE = ', '
EMPTYSTRING = ''
MAXLINELEN = 78
NONASCII = re.compile('[^\s!-~]')
# Headers from the original that we want to keep in the wrapper.  These are
# actually regexps matched with re.match so they match anything that starts
# with the given string unless they end with '$'.
KEEPERS = (
    'archived-at',
    'date',
    'in-reply-to',
    'list-',
    'precedence',
    'references',
    'subject',
    'to',
    'x-mailman-',
    )


def munged_headers(mlist, msg, msgdata):
    # This returns a list of tuples (header, content) where header is the
    # name of a header to be added to or replaced in the wrapper or message
    # for DMARC mitigation.  It sets From: to the string
    # 'original From: display name' via 'list name' <list posting address>
    # and adds the original From: to Reply-To: or Cc: per the following.
    # Our goals for this process are not completely compatible, so we do
    # the best we can.  Our goals are:
    # 1) as long as the list is not anonymous, the original From: address
    #    should be obviously exposed, i.e. not just in a header that MUAs
    #    don't display.
    # 2) the original From: address should not be in a comment or display
    #    name in the new From: because it is claimed that multiple domains
    #    in any fields in From: are indicative of spamminess.  This means
    #    it should be in Reply-To: or Cc:.
    # 3) the behavior of an MUA doing a 'reply' or 'reply all' should be
    #    consistent regardless of whether or not the From: is munged.
    # Goal 3) implies sometimes the original From: should be in Reply-To:
    # and sometimes in Cc:, and even so, this goal won't be achieved in
    # all cases with all MUAs.  In cases of conflict, the above ordering of
    # goals is priority order.
    #
    # Be as robust as possible here.
    all_froms = getaddresses(msg.get_all('from', []))
    # Strip the nulls and bad emails.
    froms = [email for email in all_froms if '@' in email[1]]
    if len(froms) == 1:
        realname, email = original_from = froms[0]
    else:
        # No From: or multiple addresses.  Just punt and take
        # the get_sender result.
        realname = ''
        email = msgdata['original_sender']
        original_from = (realname, email)
    # If there was no display name in the email header, see if we have a
    # matching member with a display name.
    if len(realname) == 0:
        member = mlist.members.get_member(email)
        if member:
            realname = member.display_name or email
        else:
            realname = email
    # Remove the domain from realname if it looks like an email address.
    realname = re.sub(r'@([^ .]+\.)+[^ .]+$', '---', realname)
    # Make a display name and RFC 2047 encode it if necessary.  This is
    # difficult and kludgy.  If the realname came from From: it should be
    # ASCII or RFC 2047 encoded.  If it came from the member record, it should
    # be a string.  If it's from the email address, it should be an ASCII
    # string.  In any case, ensure it's an unencoded string.
    realname_bits = []
    for fragment, charset in decode_header(realname):
        if not charset:
            # Character set should be ASCII, but use iso-8859-1 anyway.
            charset = 'iso-8859-1'
        if not isinstance(fragment, str):
            realname_bits.append(str(fragment, charset, errors='replace'))
        else:
            realname_bits.append(fragment)
    # The member's display name is a string.
    realname = EMPTYSTRING.join(realname_bits)
    # Ensure the i18n context is the list's preferred_language.
    with _.using(mlist.preferred_language.code):
        via = _('$realname via $mlist.display_name')
    # Get an RFC 2047 encoded header string.
    display_name = str(Header(via, mlist.preferred_language.charset))
    value = [('From', formataddr((display_name, mlist.posting_address)))]
    # We've made the munged From:.  Now put the original in Reply-To: or Cc:
    if mlist.reply_goes_to_list is ReplyToMunging.no_munging:
        # Add original from to Reply-To:
        add_to = 'Reply-To'
    else:
        # Add original from to Cc:
        add_to = 'Cc'
    original = getaddresses(msg.get_all(add_to, []))
    if original_from[1] not in [x[1] for x in original]:
        original.append(original_from)
    value.append((add_to, COMMASPACE.join(formataddr(x) for x in original)))
    return value


def munge_from(mlist, msg, msgdata):
    for key, value in munged_headers(mlist, msg, msgdata):
        del msg[key]
        msg[key] = value
    return


def wrap_message(mlist, msg, msgdata):
    # Create a wrapper message around the original.
    #
    # There are various headers in msg that we don't want, so we basically
    # make a copy of the message, then delete almost everything and set/copy
    # what we want.
    original_msg = copy.deepcopy(msg)
    for key in msg:
        keep = False
        for keeper in KEEPERS:
            if re.match(keeper, key, re.IGNORECASE):
                keep = True
                break
        if not keep:
            del msg[key]
    msg['MIME-Version'] = '1.0'
    msg['Message-ID'] = make_msgid()
    for key, value in munged_headers(mlist, original_msg, msgdata):
        msg[key] = value
    # Are we including dmarc_wrapped_message_text?
    if len(mlist.dmarc_wrapped_message_text) > 0:
        part1 = MIMEText(
            wrap(mlist.dmarc_wrapped_message_text),
            'plain',
            mlist.preferred_language.charset)
        part1['Content-Disposition'] = 'inline'
        part2 = MIMEMessage(original_msg)
        part2['Content-Disposition'] = 'inline'
        msg['Content-Type'] = 'multipart/mixed'
        msg.set_payload([part1, part2])
    else:
        msg['Content-Type'] = 'message/rfc822'
        msg['Content-Disposition'] = 'inline'
        msg.set_payload([original_msg])
    return


def process(mlist, msg, msgdata):
    # If we're mitigating on policy and we have no hit, return.
    if not msgdata.get('dmarc') and not mlist.dmarc_mitigate_unconditionally:
        return
    # If we're not mitigating, return.
    if mlist.dmarc_mitigate_action is DMARCMitigateAction.no_mitigation:
        return
    if mlist.anonymous_list:
        # DMARC mitigation is not required for anonymous lists.
        return
    if msgdata.get('dmarc') or mlist.dmarc_mitigate_unconditionally:
        if mlist.dmarc_mitigate_action is DMARCMitigateAction.munge_from:
            munge_from(mlist, msg, msgdata)
        elif mlist.dmarc_mitigate_action is DMARCMitigateAction.wrap_message:
            wrap_message(mlist, msg, msgdata)
        else:
            # We can get here if DMARCMitigateAction is reject or discard but
            # the From: domain has no reject or quarantine policy and
            # mlist.dmarc_mitigate_unconditionally is True.  Log and ignore
            # this.
            log.error('Invalid DMARC combination for list: %s', mlist)
            return
    else:
        raise AssertionError(
            'handlers/dmarc.py: no hit and unconditional is False')


@public
@implementer(IHandler)
class DMARC:
    """Apply DMARC mitigations."""

    name = 'dmarc'
    description = _('Apply DMARC mitigations.')

    def process(self, mlist, msg, msgdata):
        """See `IHandler`."""
        process(mlist, msg, msgdata)
