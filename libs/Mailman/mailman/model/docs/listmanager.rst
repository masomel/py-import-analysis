========================
The mailing list manager
========================

The ``IListManager`` is how you create, delete, and retrieve mailing list
objects.

    >>> from mailman.interfaces.listmanager import IListManager
    >>> from zope.component import getUtility
    >>> list_manager = getUtility(IListManager)


Creating a mailing list
=======================

Creating the list returns the newly created IMailList object.

    >>> from mailman.interfaces.mailinglist import IMailingList
    >>> mlist = list_manager.create('test@example.com')
    >>> IMailingList.providedBy(mlist)
    True

All lists with identities have a short name, a host name, a fully qualified
listname, and an `RFC 2369`_ list id.  This latter will not change even if the
mailing list moves to a different host, so it is what uniquely distinguishes
the mailing list to the system.

    >>> print(mlist.list_name)
    test
    >>> print(mlist.mail_host)
    example.com
    >>> print(mlist.fqdn_listname)
    test@example.com
    >>> print(mlist.list_id)
    test.example.com


Deleting a mailing list
=======================

Use the list manager to delete a mailing list.

    >>> list_manager.delete(mlist)
    >>> sorted(list_manager.names)
    []

After deleting the list, you can create it again.

    >>> mlist = list_manager.create('test@example.com')
    >>> print(mlist.fqdn_listname)
    test@example.com


Retrieving a mailing list
=========================

When a mailing list exists, you can ask the list manager for it and you will
always get the same object back.

    >>> mlist_2 = list_manager.get('test@example.com')
    >>> mlist_2 is mlist
    True

You can also get a mailing list by it's list id.

    >>> mlist_2 = list_manager.get_by_list_id('test.example.com')
    >>> mlist_2 is mlist
    True

If you try to get a list that doesn't existing yet, you get ``None``.

    >>> print(list_manager.get('test_2@example.com'))
    None
    >>> print(list_manager.get_by_list_id('test_2.example.com'))
    None

You also get ``None`` if the list name is invalid.

    >>> print(list_manager.get('foo'))
    None


Iterating over all mailing lists
================================

Once you've created a bunch of mailing lists, you can use the list manager to
iterate over the mailing list objects, the list posting addresses, or the list
address components.
::

    >>> mlist_3 = list_manager.create('test_3@example.com')
    >>> mlist_4 = list_manager.create('test_4@example.com')

    >>> for name in sorted(list_manager.names):
    ...     print(name)
    test@example.com
    test_3@example.com
    test_4@example.com

    >>> for list_id in sorted(list_manager.list_ids):
    ...     print(list_id)
    test.example.com
    test_3.example.com
    test_4.example.com

    >>> for fqdn_listname in sorted(m.fqdn_listname
    ...                             for m in list_manager.mailing_lists):
    ...     print(fqdn_listname)
    test@example.com
    test_3@example.com
    test_4@example.com

    >>> for list_name, mail_host in sorted(list_manager.name_components):
    ...     print(list_name, '@', mail_host)
    test   @ example.com
    test_3 @ example.com
    test_4 @ example.com


.. _`RFC 2369`: http://www.faqs.org/rfcs/rfc2369.html
