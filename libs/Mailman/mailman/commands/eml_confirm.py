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

"""The 'confirm' email command."""

from mailman.core.i18n import _
from mailman.interfaces.command import ContinueProcessing, IEmailCommand
from mailman.interfaces.subscriptions import ISubscriptionManager, TokenOwner
from public import public
from zope.interface import implementer


@public
@implementer(IEmailCommand)
class Confirm:
    """The email 'confirm' command."""

    name = 'confirm'
    argument_description = 'token'
    description = _('Confirm a subscription request.')
    short_description = description

    def process(self, mlist, msg, msgdata, arguments, results):
        """See `IEmailCommand`."""
        # The token must be in the arguments.
        if len(arguments) == 0:
            print(_('No confirmation token found'), file=results)
            return ContinueProcessing.no
        # Make sure we don't try to confirm the same token more than once.
        token = arguments[0]
        tokens = getattr(results, 'confirms', set())
        if token in tokens:
            # Do not try to confirm this one again.
            return ContinueProcessing.yes
        tokens.add(token)
        results.confirms = tokens
        try:
            new_token, token_owner, member = ISubscriptionManager(
                mlist).confirm(token)
            if new_token is None:
                assert token_owner is TokenOwner.no_one, token_owner
                # We can't assert anything about member.  It will be None when
                # the workflow we're confirming is an unsubscription request,
                # and non-None when we're confirming a subscription request.
                # This class doesn't know which is happening.
                succeeded = True
            elif token_owner is TokenOwner.moderator:
                # This must have been a confirm-then-moderator subscription.
                assert new_token != token
                assert member is None, member
                succeeded = True
            else:
                assert token_owner is not TokenOwner.no_one, token_owner
                assert member is None, member
                succeeded = False
        except LookupError:
            # The token must not exist in the database.
            succeeded = False
        if succeeded:
            print(_('Confirmed'), file=results)
            return ContinueProcessing.yes
        print(_('Confirmation token did not match'), file=results)
        return ContinueProcessing.no
