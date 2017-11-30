# Copyright (C) 2006-2017 by the Free Software Foundation, Inc.
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

"""Model for addresses."""

from email.utils import formataddr
from mailman.database.model import Model
from mailman.database.types import SAUnicode
from mailman.interfaces.address import (
    AddressVerificationEvent, IAddress, IEmailValidator)
from mailman.utilities.datetime import now
from public import public
from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import backref, relationship
from zope.component import getUtility
from zope.event import notify
from zope.interface import implementer


@public
@implementer(IAddress)
class Address(Model):
    """See `IAddress`."""

    __tablename__ = 'address'

    id = Column(Integer, primary_key=True)
    email = Column(SAUnicode, index=True)
    _original = Column(SAUnicode)
    display_name = Column(SAUnicode)
    _verified_on = Column('verified_on', DateTime)
    registered_on = Column(DateTime)

    user_id = Column(Integer, ForeignKey('user.id'), index=True)

    preferences_id = Column(Integer, ForeignKey('preferences.id'), index=True)
    preferences = relationship(
        'Preferences', backref=backref('address', uselist=False))

    def __init__(self, email, display_name):
        super().__init__()
        getUtility(IEmailValidator).validate(email)
        lower_case = email.lower()
        self.email = lower_case
        self.display_name = display_name
        self._original = (None if lower_case == email else email)
        self.registered_on = now()

    def __str__(self):
        addr = (self.email if self._original is None else self._original)
        return formataddr((self.display_name, addr))

    def __repr__(self):
        verified = ('verified' if self.verified_on else 'not verified')
        address_str = str(self)
        if self._original is None:
            return '<Address: {} [{}] at {:#x}>'.format(
                address_str, verified, id(self))
        else:
            return '<Address: {} [{}] key: {} at {:#x}>'.format(
                address_str, verified, self.email, id(self))

    @property
    def verified_on(self):
        return self._verified_on

    @verified_on.setter
    def verified_on(self, timestamp):
        self._verified_on = timestamp
        notify(AddressVerificationEvent(self))

    @property
    def original_email(self):
        return (self.email if self._original is None else self._original)
