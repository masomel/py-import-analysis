=================================
Application level list life cycle
=================================

The low-level way to create and delete a mailing list is to use the
``IListManager`` interface.  This interface simply adds or removes the
appropriate database entries to record the list's creation.

There is a higher level interface for creating and deleting mailing lists
which performs additional tasks such as:

 * validating the list's posting address (which also serves as the list's
   fully qualified name);
 * ensuring that the list's domain is registered;
 * :ref:`applying a list style <list-creation-styles>` to the new list;
 * creating and assigning list owners;
 * notifying watchers of list creation;
 * creating ancillary artifacts (such as the list's on-disk directory)


Creating a list with owners
===========================

You can also specify a list of owner email addresses.  If these addresses are
not yet known, they will be registered, and new users will be linked to them.
::

    >>> owners = [
    ...     'aperson@example.com',
    ...     'bperson@example.com',
    ...     'cperson@example.com',
    ...     'dperson@example.com',
    ...     ]

    >>> ant = create_list('ant@example.com', owners)
    >>> dump_list(address.email for address in ant.owners.addresses)
    aperson@example.com
    bperson@example.com
    cperson@example.com
    dperson@example.com

None of the owner addresses are verified.

    >>> any(address.verified_on is not None
    ...     for address in ant.owners.addresses)
    False

However, all addresses are linked to users.

    >>> from mailman.interfaces.usermanager import IUserManager
    >>> from zope.component import getUtility
    >>> user_manager = getUtility(IUserManager)
    >>> for address in owners:
    ...     user = user_manager.get_user(address)
    ...     print(int(user.user_id.int), list(user.addresses)[0])
    1 aperson@example.com
    2 bperson@example.com
    3 cperson@example.com
    4 dperson@example.com

If you create a mailing list with owner addresses that are already known to
the system, they won't be created again.

    >>> bee = create_list('bee@example.com', owners)
    >>> from operator import attrgetter
    >>> for user in sorted(bee.owners.users, key=attrgetter('user_id')):
    ...     print(int(user.user_id.int), list(user.addresses)[0])
    1 aperson@example.com
    2 bperson@example.com
    3 cperson@example.com
    4 dperson@example.com


Deleting a list
===============

Removing a mailing list deletes the list, all its subscribers, and any related
artifacts.
::

    >>> from mailman.app.lifecycle import remove_list
    >>> remove_list(bee)

    >>> from mailman.interfaces.listmanager import IListManager
    >>> print(getUtility(IListManager).get('bee@example.com'))
    None

We should now be able to completely recreate the mailing list.

    >>> buzz = create_list('bee@example.com', owners)
    >>> dump_list(address.email for address in bee.owners.addresses)
    aperson@example.com
    bperson@example.com
    cperson@example.com
    dperson@example.com
