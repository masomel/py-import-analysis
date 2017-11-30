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

"""A mailing list manager."""

from mailman.database.transaction import dbconnection
from mailman.interfaces.address import InvalidEmailAddressError
from mailman.interfaces.listmanager import (
    IListManager, ListAlreadyExistsError, ListCreatedEvent, ListCreatingEvent,
    ListDeletedEvent, ListDeletingEvent)
from mailman.interfaces.requests import IListRequests
from mailman.model.autorespond import AutoResponseRecord
from mailman.model.bans import Ban
from mailman.model.mailinglist import (
    IAcceptableAliasSet, ListArchiver, MailingList)
from mailman.model.mime import ContentFilter
from mailman.utilities.datetime import now
from mailman.utilities.queries import QuerySequence
from public import public
from zope.event import notify
from zope.interface import implementer


@public
@implementer(IListManager)
class ListManager:
    """An implementation of the `IListManager` interface."""

    @dbconnection
    def create(self, store, fqdn_listname):
        """See `IListManager`."""
        fqdn_listname = fqdn_listname.lower()
        listname, at, hostname = fqdn_listname.partition('@')
        if len(hostname) == 0:
            raise InvalidEmailAddressError(fqdn_listname)
        list_id = '{}.{}'.format(listname, hostname)
        notify(ListCreatingEvent(fqdn_listname))
        mlist = store.query(MailingList).filter_by(_list_id=list_id).first()
        if mlist:
            raise ListAlreadyExistsError(fqdn_listname)
        mlist = MailingList(fqdn_listname)
        mlist.created_at = now()
        store.add(mlist)
        notify(ListCreatedEvent(mlist))
        return mlist

    @dbconnection
    def get(self, store, fqdn_listname):
        """See `IListManager`."""
        listname, at, hostname = fqdn_listname.partition('@')
        list_id = '{}.{}'.format(listname, hostname)
        return store.query(MailingList).filter_by(_list_id=list_id).first()

    @dbconnection
    def get_by_list_id(self, store, list_id):
        """See `IListManager`."""
        return store.query(MailingList).filter_by(_list_id=list_id).first()

    @dbconnection
    def delete(self, store, mlist):
        """See `IListManager`."""
        fqdn_listname = mlist.fqdn_listname
        notify(ListDeletingEvent(mlist))
        # First delete information associated with the mailing list.
        IAcceptableAliasSet(mlist).clear()
        IListRequests(mlist).clear()
        store.query(AutoResponseRecord).filter_by(mailing_list=mlist).delete()
        store.query(ContentFilter).filter_by(mailing_list=mlist).delete()
        store.query(ListArchiver).filter_by(mailing_list=mlist).delete()
        store.query(Ban).filter_by(list_id=mlist.list_id).delete()
        store.delete(mlist)
        notify(ListDeletedEvent(fqdn_listname))

    @property
    @dbconnection
    def mailing_lists(self, store):
        """See `IListManager`."""
        yield from store.query(MailingList).order_by(
            MailingList._list_id).all()

    @dbconnection
    def __iter__(self, store):
        """See `IListManager`."""
        yield from store.query(MailingList).order_by(
            MailingList._list_id).all()

    @property
    @dbconnection
    def names(self, store):
        """See `IListManager`."""
        result_set = store.query(MailingList)
        for mail_host, list_name in result_set.values(MailingList.mail_host,
                                                      MailingList.list_name):
            yield '{}@{}'.format(list_name, mail_host)

    @property
    @dbconnection
    def list_ids(self, store):
        """See `IListManager`."""
        result_set = store.query(MailingList)
        for list_id in result_set.values(MailingList._list_id):
            assert isinstance(list_id, tuple) and len(list_id) == 1
            yield list_id[0]

    @property
    @dbconnection
    def name_components(self, store):
        """See `IListManager`."""
        result_set = store.query(MailingList)
        for mail_host, list_name in result_set.values(MailingList.mail_host,
                                                      MailingList.list_name):
            yield list_name, mail_host

    @dbconnection
    def find(self, store, *, advertised=None, mail_host=None):
        query = store.query(MailingList)
        if advertised is not None:
            query = query.filter_by(advertised=advertised)
        if mail_host is not None:
            query = query.filter_by(mail_host=mail_host)
        query = query.order_by(MailingList._list_id)
        return QuerySequence(query)
