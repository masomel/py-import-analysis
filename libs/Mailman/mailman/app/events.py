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

"""Global events."""

from mailman.app import domain, membership, moderator, subscriptions
from mailman.core import i18n, switchboard
from mailman.languages import manager as language_manager
from mailman.styles import manager as style_manager
from mailman.utilities import passwords
from public import public
from zope import event


@public
def initialize():
    """Initialize global event subscribers."""
    event.subscribers.extend([
        domain.handle_DomainDeletingEvent,
        i18n.handle_ConfigurationUpdatedEvent,
        language_manager.handle_ConfigurationUpdatedEvent,
        membership.handle_SubscriptionEvent,
        moderator.handle_ListDeletingEvent,
        passwords.handle_ConfigurationUpdatedEvent,
        style_manager.handle_ConfigurationUpdatedEvent,
        subscriptions.handle_ListDeletingEvent,
        subscriptions.handle_SubscriptionConfirmationNeededEvent,
        subscriptions.handle_UnsubscriptionConfirmationNeededEvent,
        switchboard.handle_ConfigurationUpdatedEvent,
        ])
