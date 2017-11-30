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

"""One last digest."""

from mailman.database.model import Model
from mailman.database.types import Enum
from mailman.interfaces.digests import IOneLastDigest
from mailman.interfaces.member import DeliveryMode
from public import public
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from zope.interface import implementer


@public
@implementer(IOneLastDigest)
class OneLastDigest(Model):
    """See `IOneLastDigest`."""

    __tablename__ = 'onelastdigest'

    id = Column(Integer, primary_key=True)

    mailing_list_id = Column(Integer, ForeignKey('mailinglist.id'))
    mailing_list = relationship('MailingList')

    address_id = Column(Integer, ForeignKey('address.id'))
    address = relationship('Address')

    delivery_mode = Column(Enum(DeliveryMode))

    def __init__(self, mailing_list, address, delivery_mode):
        self.mailing_list = mailing_list
        self.address = address
        self.delivery_mode = delivery_mode
