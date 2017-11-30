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

"""RFC 2369 List-* and related headers."""

import logging

from email.utils import formataddr
from mailman.core.i18n import _
from mailman.handlers.cook_headers import uheader
from mailman.interfaces.archiver import ArchivePolicy
from mailman.interfaces.handler import IHandler
from mailman.interfaces.mailinglist import IListArchiverSet
from public import public
from zope.interface import implementer


CONTINUATION = ',\n\t'

log = logging.getLogger('mailman.archiver')


def process(mlist, msg, msgdata):
    """Add the RFC 2369 List-* and related headers."""
    # Some people really hate the List-* headers.  It seems that the free
    # version of Eudora (possibly on for some platforms) does not hide these
    # headers by default, pissing off their users.  Too bad.  Fix the MUAs.
    if not mlist.include_rfc2369_headers:
        return
    list_id = '{0.list_name}.{0.mail_host}'.format(mlist)
    if mlist.description:
        # Don't wrap the header since here we just want to get it properly RFC
        # 2047 encoded.
        i18ndesc = uheader(mlist, mlist.description, 'List-Id', maxlinelen=998)
        listid_h = formataddr((str(i18ndesc), list_id))
    else:
        # Without a description, we need to ensure the MUST brackets.
        listid_h = '<{}>'.format(list_id)
    # No other agent should add a List-ID header except Mailman.
    del msg['list-id']
    msg['List-Id'] = listid_h
    # For internally crafted messages, we also add a (nonstandard),
    # "X-List-Administrivia: yes" header.  For all others (i.e. those coming
    # from list posts), we add a bunch of other RFC 2369 headers.
    requestaddr = mlist.request_address
    headers = []
    # XXX reduced_list_headers used to suppress List-Help, List-Subject, and
    # List-Unsubscribe from UserNotification.  That doesn't seem to make sense
    # any more, so always add those three headers (others will still be
    # suppressed).
    headers.extend((
        ('List-Help', '<mailto:{}?subject=help>'.format(requestaddr)),
        ('List-Unsubscribe', '<mailto:{}>'.format(mlist.leave_address)),
        ('List-Subscribe', '<mailto:{}>'.format(mlist.join_address)),
        ))
    if not msgdata.get('reduced_list_headers'):
        # List-Post: is controlled by a separate attribute, which is somewhat
        # misnamed.  RFC 2369 requires a value of NO if posting is not
        # allowed, i.e. for an announce-only list.
        list_post = ('<mailto:{}>'.format(mlist.posting_address)
                     if mlist.allow_list_posts
                     else 'NO')
        headers.append(('List-Post', list_post))
        # Add RFC 2369 and 5064 archiving headers, if archiving is enabled.
        if mlist.archive_policy is not ArchivePolicy.never:
            archiver_set = IListArchiverSet(mlist)
            for archiver in archiver_set.archivers:
                if not archiver.is_enabled:
                    continue
                # Watch out for exceptions in the archiver plugin.
                try:
                    archiver_url = archiver.system_archiver.list_url(mlist)
                except Exception:
                    log.exception('Exception in "{}" archiver'.format(
                        archiver.system_archiver.name))
                    archiver_url = None
                if archiver_url is not None:
                    headers.append(('List-Archive',
                                    '<{}>'.format(archiver_url)))
                try:
                    permalink = archiver.system_archiver.permalink(mlist, msg)
                except Exception:
                    log.exception('Exception in "{}" archiver'.format(
                        archiver.system_archiver.name))
                    permalink = None
                if permalink is not None:
                    headers.append(('Archived-At', '<{}>'.format(permalink)))
    # XXX RFC 2369 also defines a List-Owner header which we are not currently
    # supporting, but should.
    #
    # Some headers will appear more than once in the new set, e.g. the
    # List-Archive and Archived-At headers.  We want to delete any RFC 2369
    # headers from the original message, but make sure to preserve all of the
    # new headers we're adding.  Go through the list of new headers twice,
    # first removing any old ones, then adding all the new ones.
    for h, v in headers:
        del msg[h]
    for h, v in sorted(headers):
        # Wrap these lines if they are too long.  78 character width probably
        # shouldn't be hardcoded, but is at least text-MUA friendly.  The
        # adding of 2 is for the colon-space separator.
        if len(h) + 2 + len(v) > 78:
            v = CONTINUATION.join(v.split(', '))
        msg[h] = v


@public
@implementer(IHandler)
class RFC2369:
    """Add the RFC 2369 List-* headers."""

    name = 'rfc-2369'
    description = _('Add the RFC 2369 List-* headers.')

    def process(self, mlist, msg, msgdata):
        """See `IHandler`."""
        process(mlist, msg, msgdata)
