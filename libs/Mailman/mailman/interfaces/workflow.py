# Copyright (C) 2015-2017 by the Free Software Foundation, Inc.
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

"""Interfaces describing the state of a workflow."""

from public import public
from zope.interface import Attribute, Interface


@public
class IWorkflowState(Interface):
    """The state of a workflow."""

    token = Attribute('A unique key identifying the workflow instance.')

    step = Attribute("This workflow's next step.")

    data = Attribute('Additional data (may be JSON-encoded).')


@public
class IWorkflowStateManager(Interface):
    """The workflow states manager."""

    def save(token, step, data=None):
        """Save the state of a workflow.

        :param token: A unique token identifying this workflow instance.
        :type token: str
        :param step: The next step for this workflow.
        :type step: str
        :param data: Additional data (workflow-specific).
        :type data: str
        """

    def restore(token):
        """Get the saved state for a workflow or None if nothing was saved.

        :param token: A unique token identifying this workflow instance.
        :type token: str
        :return: The saved state associated with this name/token pair, or None
            if the pair isn't in the database.
        :rtype: ``IWorkflowState``
        """

    def discard(token):
        """Throw away the saved state for a workflow.

        :param token: A unique token identifying this workflow instance.
        :type token: str
        """

    count = Attribute('The number of saved workflows in the database.')
