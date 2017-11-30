# Copyright (C) 2008-2017 by the Free Software Foundation, Inc.
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

"""Initialize the email commands."""

from mailman.config import config
from mailman.interfaces.command import IEmailCommand
from mailman.utilities.modules import find_components
from public import public
from zope.interface.verify import verifyObject


@public
def initialize():
    """Initialize the email commands."""
    for command_class in find_components('mailman.commands', IEmailCommand):
        command = command_class()
        verifyObject(IEmailCommand, command)
        assert command_class.name not in config.commands, (
            'Duplicate email command "{}" found in {}'.format(
                command_class.name, command_class.__module__))
        config.commands[command_class.name] = command_class()
