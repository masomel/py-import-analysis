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

"""Autoresponder records."""

from mailman.database.model import Model
from mailman.database.transaction import dbconnection
from mailman.database.types import Enum
from mailman.interfaces.autorespond import (
    IAutoResponseRecord, IAutoResponseSet, Response)
from mailman.utilities.datetime import today
from public import public
from sqlalchemy import Column, Date, ForeignKey, Integer, desc
from sqlalchemy.orm import relationship
from zope.interface import implementer


@public
@implementer(IAutoResponseRecord)
class AutoResponseRecord(Model):
    """See `IAutoResponseRecord`."""

    __tablename__ = 'autoresponserecord'

    id = Column(Integer, primary_key=True)

    address_id = Column(Integer, ForeignKey('address.id'), index=True)
    address = relationship('Address')

    mailing_list_id = Column(Integer, ForeignKey('mailinglist.id'), index=True)
    mailing_list = relationship('MailingList')

    response_type = Column(Enum(Response))
    date_sent = Column(Date)

    def __init__(self, mailing_list, address, response_type):
        self.mailing_list = mailing_list
        self.address = address
        self.response_type = response_type
        self.date_sent = today()


@public
@implementer(IAutoResponseSet)
class AutoResponseSet:
    """See `IAutoResponseSet`."""

    def __init__(self, mailing_list):
        self._mailing_list = mailing_list

    @dbconnection
    def todays_count(self, store, address, response_type):
        """See `IAutoResponseSet`."""
        return store.query(AutoResponseRecord).filter_by(
            address=address,
            mailing_list=self._mailing_list,
            response_type=response_type,
            date_sent=today()).count()

    @dbconnection
    def response_sent(self, store, address, response_type):
        """See `IAutoResponseSet`."""
        response = AutoResponseRecord(
            self._mailing_list, address, response_type)
        store.add(response)

    @dbconnection
    def last_response(self, store, address, response_type):
        """See `IAutoResponseSet`."""
        results = store.query(AutoResponseRecord).filter_by(
            address=address,
            mailing_list=self._mailing_list,
            response_type=response_type
            ).order_by(desc(AutoResponseRecord.date_sent))
        return (None if results.count() == 0 else results.first())
