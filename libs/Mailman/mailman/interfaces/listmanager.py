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

"""Interface for list storage, deleting, and finding."""

from mailman.interfaces.errors import MailmanError
from public import public
from zope.interface import Attribute, Interface


@public
class ListAlreadyExistsError(MailmanError):
    """Attempted to create a mailing list that already exists.

    Mailing list objects must be uniquely named by their fully qualified list
    name.
    """


@public
class NoSuchListError(MailmanError):
    """Attempt to access a mailing list that does not exist."""

    def __init__(self, fqdn_listname):
        self.fqdn_listname = fqdn_listname

    def __str__(self):
        return 'No such mailing list: {0.fqdn_listname}'.format(self)


@public
class ListCreatingEvent:
    """A mailing list is about to be created."""

    def __init__(self, fqdn_listname):
        self.fqdn_listname = fqdn_listname


@public
class ListCreatedEvent:
    """A mailing list was created."""

    def __init__(self, mlist):
        self.mailing_list = mlist


@public
class ListDeletingEvent:
    """A mailing list is about to be deleted."""

    def __init__(self, mailing_list):
        self.mailing_list = mailing_list


@public
class ListDeletedEvent:
    """A mailing list was deleted."""

    def __init__(self, fqdn_listname):
        self.fqdn_listname = fqdn_listname


@public
class IListManager(Interface):
    """The interface of the global list manager.

    The list manager manages `IMailingList` objects.  You can add and remove
    `IMailingList` objects from the list manager, and you can retrieve them
    from the manager via their fully qualified list name, e.g.:
    `mylist@example.com`.
    """

    def create(fqdn_listname):
        """Create a mailing list with the given name.

        :param fqdn_listname: The fully qualified name of the mailing list,
            e.g. `mylist@example.com`.
        :type fqdn_listname: Unicode
        :return: The newly created `IMailingList`.
        :raise `ListAlreadyExistsError` if the named list already exists.
        """

    def get(fqdn_listname):
        """Return the mailing list with the given name, if it exists.

        :param fqdn_listname: The fully qualified name of the mailing list.
        :type fqdn_listname: Unicode.
        :return: the matching `IMailingList` or None if the named list does
            not exist.
        """

    def get_by_list_id(list_id):
        """Return the mailing list with the given list id, if it exists.

        :param fqdn_listname: The fully qualified name of the mailing list.
        :type fqdn_listname: Unicode.
        :return: the matching `IMailingList` or None if the named list does
            not exist.
        """

    def delete(mlist):
        """Remove the mailing list from the database.

        :param mlist: The mailing list to delete.
        :type mlist: `IMailingList`
        """

    mailing_lists = Attribute(
        """An iterator over all the mailing list objects.

        The mailing lists are returned in order sorted by `list_id`.
        """)

    def __iter__():
        """An iterator over all the mailing lists.

        :return: iterator over `IMailingList`.
        """

    names = Attribute(
        """An iterator over the fully qualified list names of all mailing
        lists managed by this list manager.""")

    list_ids = Attribute(
        """An iterator over the list ids of all mailing lists managed by this
        list manager.""")

    name_components = Attribute(
        """An iterator over the 2-tuple of (list_name, mail_host) for all
        mailing lists managed by this list manager.""")

    def find(*, advertised=None, mail_host=None):
        """Search for mailing lists matching some criteria.

        The keyword arguments are mailing list properties that will be
        filtered upon.

        :return: The list of filtered mailing lists.
        :rtype: list of `IMailingList`
        """
