================
The user manager
================

The ``IUserManager`` is how you create, delete, and manage users.

    >>> from mailman.interfaces.usermanager import IUserManager
    >>> from zope.component import getUtility
    >>> user_manager = getUtility(IUserManager)


Creating users
==============

There are several ways you can create a user object.  The simplest is to
create a `blank` user by not providing an address or real name at creation
time.  This user will have an empty string as their real name, but will not
have a password.
::

    >>> from mailman.interfaces.user import IUser
    >>> from zope.interface.verify import verifyObject
    >>> user = user_manager.create_user()
    >>> verifyObject(IUser, user)
    True

    >>> dump_list(address.email for address in user.addresses)
    *Empty*
    >>> print(user.display_name)
    <BLANKLINE>
    >>> print(user.password)
    None

The user has preferences, but none of them will be specified.

    >>> print(user.preferences)
    <Preferences ...>

A user can be assigned a real name.

    >>> user.display_name = 'Anne Person'
    >>> dump_list(user.display_name for user in user_manager.users)
    Anne Person

A user can be assigned a password.

    >>> user.password = 'secret'
    >>> dump_list(user.password for user in user_manager.users)
    secret

You can also create a user with an address to start out with.

    >>> user_2 = user_manager.create_user('bperson@example.com')
    >>> verifyObject(IUser, user_2)
    True
    >>> dump_list(address.email for address in user_2.addresses)
    bperson@example.com
    >>> dump_list(user.display_name for user in user_manager.users)
    <BLANKLINE>
    Anne Person

As above, you can assign a real name to such users.

    >>> user_2.display_name = 'Ben Person'
    >>> dump_list(user.display_name for user in user_manager.users)
    Anne Person
    Ben Person

You can also create a user with just a real name.

    >>> user_3 = user_manager.create_user(display_name='Claire Person')
    >>> verifyObject(IUser, user_3)
    True
    >>> dump_list(address.email for address in user.addresses)
    *Empty*
    >>> dump_list(user.display_name for user in user_manager.users)
    Anne Person
    Ben Person
    Claire Person

Finally, you can create a user with both an address and a real name.

    >>> user_4 = user_manager.create_user('dperson@example.com', 'Dan Person')
    >>> verifyObject(IUser, user_3)
    True
    >>> dump_list(address.email for address in user_4.addresses)
    dperson@example.com
    >>> dump_list(address.display_name for address in user_4.addresses)
    Dan Person
    >>> dump_list(user.display_name for user in user_manager.users)
    Anne Person
    Ben Person
    Claire Person
    Dan Person


Deleting users
==============

You delete users by going through the user manager.  The deleted user is no
longer available through the user manager iterator.

    >>> user_manager.delete_user(user)
    >>> dump_list(user.display_name for user in user_manager.users)
    Ben Person
    Claire Person
    Dan Person


Finding users
=============

You can ask the user manager to find the ``IUser`` that controls a particular
email address.  You'll get back the original user object if it's found.  Note
that the ``.get_user()`` method takes a string email address, not an
``IAddress`` object.

    >>> address = list(user_4.addresses)[0]
    >>> found_user = user_manager.get_user(address.email)
    >>> found_user
    <User "Dan Person" (...) at ...>
    >>> found_user is user_4
    True

If the address is not in the user database or does not have a user associated
with it, you will get ``None`` back.

    >>> print(user_manager.get_user('zperson@example.com'))
    None
    >>> user_4.unlink(address)
    >>> print(user_manager.get_user(address.email))
    None

Users can also be found by their unique user id.

    >>> found_user = user_manager.get_user_by_id(user_4.user_id)
    >>> user_4
    <User "Dan Person" (...) at ...>
    >>> found_user
    <User "Dan Person" (...) at ...>
    >>> user_4.user_id == found_user.user_id
    True

If a non-existent user id is given, None is returned.

    >>> from uuid import UUID
    >>> print(user_manager.get_user_by_id(UUID(int=801)))
    None


Finding all members
===================

The user manager can return all the members known to the system.

    >>> mlist = create_list('test@example.com')
    >>> mlist.subscribe(list(user_2.addresses)[0])
    <Member: bperson@example.com on test@example.com as MemberRole.member>
    >>> mlist.subscribe(user_manager.create_address('eperson@example.com'))
    <Member: eperson@example.com on test@example.com as MemberRole.member>
    >>> mlist.subscribe(user_manager.create_address('fperson@example.com'))
    <Member: fperson@example.com on test@example.com as MemberRole.member>

Bart is also the owner of the mailing list.

    >>> from mailman.interfaces.member import MemberRole
    >>> mlist.subscribe(list(user_2.addresses)[0], MemberRole.owner)
    <Member: bperson@example.com on test@example.com as MemberRole.owner>

There are now four members in the system.  Sort them by address then role.

    >>> def sort_key(member):
    ...     return (member.address.email, member.role.name)
    >>> members = sorted(user_manager.members, key=sort_key)
    >>> for member in members:
    ...     print(member.mailing_list.list_id, member.address.email,
    ...           member.role)
    test.example.com bperson@example.com MemberRole.member
    test.example.com bperson@example.com MemberRole.owner
    test.example.com eperson@example.com MemberRole.member
    test.example.com fperson@example.com MemberRole.member


Creating a new user
===================

A common situation (especially during the subscription life cycle) is to
create a user linked to an address, with a preferred address.  Say for
example, we are asked to subscribe a new address we have never seen before.

    >>> cris = user_manager.make_user('cris@example.com', 'Cris Person')

Since we've never seen ``cris@example.com`` before, this call creates a new
user with the given email and display name.

    >>> cris
    <User "Cris Person" (5) at ...>

The user has a single unverified address object.

    >>> for address in cris.addresses:
    ...     print(repr(address))
    <Address: Cris Person <cris@example.com> [not verified] at ...>


Server owners
=============

Some users are designated as *server owners*.  At first there are no server
owners.

    >>> len(list(user_manager.server_owners))
    0

Dan is made a server owner.

    >>> user_4.is_server_owner = True
    >>> owners = list(user_manager.server_owners)
    >>> len(owners)
    1
    >>> owners[0]
    <User "Dan Person" (...) at ...>

Now Ben and Claire are also made server owners.

    >>> user_2.is_server_owner = True
    >>> user_3.is_server_owner = True
    >>> owners = list(user_manager.server_owners)
    >>> len(owners)
    3
    >>> from operator import attrgetter
    >>> for user in sorted(owners, key=attrgetter('display_name')):
    ...     print(user)
    <User "Ben Person" (...) at ...>
    <User "Claire Person" (...) at ...>
    <User "Dan Person" (...) at ...>

Clair retires as a server owner.

    >>> user_3.is_server_owner = False
    >>> owners = list(user_manager.server_owners)
    >>> len(owners)
    2
    >>> for user in sorted(owners, key=attrgetter('display_name')):
    ...     print(user)
    <User "Ben Person" (...) at ...>
    <User "Dan Person" (...) at ...>
