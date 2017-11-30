# Copyright (C) 2007-2017 by the Free Software Foundation, Inc.
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

"""Model for messages."""

from mailman.database.model import Model
from mailman.database.transaction import dbconnection
from mailman.database.types import SAUnicode
from mailman.interfaces.messages import IMessage
from public import public
from sqlalchemy import Column, Integer
from zope.interface import implementer


@public
@implementer(IMessage)
class Message(Model):
    """A message in the message store."""

    __tablename__ = 'message'

    id = Column(Integer, primary_key=True)
    # This is a Messge-ID field representation, not a database row id.
    message_id = Column(SAUnicode)
    message_id_hash = Column(SAUnicode)
    path = Column(SAUnicode)

    @dbconnection
    def __init__(self, store, message_id, message_id_hash, path):
        super().__init__()
        self.message_id = message_id
        self.message_id_hash = message_id_hash
        self.path = path
        store.add(self)
