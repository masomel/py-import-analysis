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

"""Implementations of the pending requests interfaces."""

from datetime import timedelta
from mailman.database.model import Model
from mailman.database.transaction import dbconnection
from mailman.database.types import Enum, SAUnicode
from mailman.interfaces.pending import IPendable, IPendings
from mailman.interfaces.requests import IListRequests, RequestType
from mailman.model.pending import Pended, PendedKeyValue
from mailman.utilities.queries import QuerySequence
from pickle import dumps, loads
from public import public
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from zope.component import getUtility
from zope.interface import implementer


@public
@implementer(IPendable)
class DataPendable(dict):
    """See `IPendable`."""

    PEND_TYPE = 'data'

    def update(self, mapping):
        # Keys and values must be strings (unicodes, but bytes values are
        # accepted for now).  Any other types for keys are a programming
        # error.  If we find a non-SAUnicode value, pickle it and encode it in
        # such a way that it will be properly reconstituted when unpended.
        clean_mapping = {}
        for key, value in mapping.items():
            assert isinstance(key, (bytes, str))
            if not isinstance(value, str):
                key = '_pck_' + key
                value = dumps(value).decode('raw-unicode-escape')
            clean_mapping[key] = value
        super().update(clean_mapping)


@public
@implementer(IListRequests)
class ListRequests:
    """See `IListRequests`."""

    def __init__(self, mailing_list):
        self.mailing_list = mailing_list

    @property
    @dbconnection
    def count(self, store):
        return store.query(_Request).filter_by(
            mailing_list=self.mailing_list).count()

    @dbconnection
    def count_of(self, store, request_type):
        return store.query(_Request).filter_by(
            mailing_list=self.mailing_list, request_type=request_type).count()

    @property
    @dbconnection
    def held_requests(self, store):
        results = store.query(_Request).filter_by(
            mailing_list=self.mailing_list)
        yield from results

    @dbconnection
    def of_type(self, store, request_type):
        return QuerySequence(
            store.query(_Request).filter_by(
                mailing_list=self.mailing_list, request_type=request_type
                ).order_by(_Request.id))

    @dbconnection
    def hold_request(self, store, request_type, key, data=None):
        if request_type not in RequestType:
            raise TypeError(request_type)
        if data is None:
            data_hash = None
        else:
            pendable = DataPendable()
            pendable.update(data)
            token = getUtility(IPendings).add(pendable, timedelta(days=5000))
            data_hash = token
        request = _Request(key, request_type, self.mailing_list, data_hash)
        store.add(request)
        # XXX The caller needs a valid id immediately, so flush the changes
        # now to the SA transaction context.  Otherwise .id would not be
        # valid.  Hopefully this has no unintended side-effects.
        store.flush()
        return request.id

    @dbconnection
    def get_request(self, store, request_id, request_type=None):
        result = store.query(_Request).get(request_id)
        if result is None or result.mailing_list != self.mailing_list:
            return None
        if request_type is not None and result.request_type != request_type:
            return None
        if result.data_hash is None:
            return result.key, None
        pendable = getUtility(IPendings).confirm(
            result.data_hash, expunge=False)
        if pendable is None:
            return None
        data = dict()
        # Unpickle any non-SAUnicode values.
        for key, value in pendable.items():
            if key.startswith('_pck_'):
                data[key[5:]] = loads(value.encode('raw-unicode-escape'))
            else:
                data[key] = value
        # Some APIs need the request type.
        data['_request_type'] = result.request_type.name
        return result.key, data

    @dbconnection
    def delete_request(self, store, request_id):
        request = store.query(_Request).get(request_id)
        if request is None:
            raise KeyError(request_id)
        # Throw away the pended data.
        getUtility(IPendings).confirm(request.data_hash)
        store.delete(request)

    @dbconnection
    def clear(self, store):
        for token, pendable in getUtility(IPendings).find(
                mlist=self.mailing_list,
                confirm=False):
            pended = store.query(Pended).filter_by(token=token).first()
            store.query(PendedKeyValue).filter_by(pended_id=pended.id).delete()
            store.delete(pended)


class _Request(Model):
    """Table for mailing list hold requests."""

    __tablename__ = '_request'

    id = Column(Integer, primary_key=True)
    key = Column(SAUnicode)
    request_type = Column(Enum(RequestType))
    data_hash = Column(SAUnicode)

    mailing_list_id = Column(Integer, ForeignKey('mailinglist.id'), index=True)
    mailing_list = relationship('MailingList')

    def __init__(self, key, request_type, mailing_list, data_hash):
        super().__init__()
        self.key = key
        self.request_type = request_type
        self.mailing_list = mailing_list
        self.data_hash = data_hash
