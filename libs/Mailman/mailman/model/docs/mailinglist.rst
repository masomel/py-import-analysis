=============
Mailing lists
=============

.. XXX 2010-06-18 BAW: This documentation needs a lot more detail.

The mailing list is a core object in Mailman.  It is uniquely identified in
the system by its *list-id* which is derived from its posting address,
i.e. the email address you would send a message to in order to post a message
to the mailing list.  The list id is defined in `RFC 2369`_.

    >>> mlist = create_list('aardvark@example.com')
    >>> print(mlist.list_id)
    aardvark.example.com
    >>> print(mlist.fqdn_listname)
    aardvark@example.com

The mailing list also has convenient attributes for accessing the list's short
name (i.e. local part) and host name.

    >>> print(mlist.list_name)
    aardvark
    >>> print(mlist.mail_host)
    example.com


Rosters
=======

Mailing list membership is represented by `rosters`.  Each mailing list has
several rosters of members, representing the subscribers to the mailing list,
the owners, the moderators, and so on.  The rosters are defined by a
membership role.

Addresses can be explicitly subscribed to a mailing list.  By default, a
subscription puts the address in the `member` role, meaning that address will
receive a copy of any message sent to the mailing list.
::

    >>> from mailman.interfaces.usermanager import IUserManager
    >>> from zope.component import getUtility
    >>> user_manager = getUtility(IUserManager)

    >>> aperson = user_manager.create_address('aperson@example.com')
    >>> bperson = user_manager.create_address('bperson@example.com')
    >>> mlist.subscribe(aperson)
    <Member: aperson@example.com on aardvark@example.com as MemberRole.member>
    >>> mlist.subscribe(bperson)
    <Member: bperson@example.com on aardvark@example.com as MemberRole.member>

Both addresses appear on the roster of members.

    >>> from operator import attrgetter
    >>> sort_key = attrgetter('address.email')

    >>> for member in sorted(mlist.members.members, key=sort_key):
    ...     print(member)
    <Member: aperson@example.com on aardvark@example.com as MemberRole.member>
    <Member: bperson@example.com on aardvark@example.com as MemberRole.member>

By explicitly specifying the role of the subscription, an address can be added
to the owner and moderator rosters.

    >>> from mailman.interfaces.member import MemberRole
    >>> mlist.subscribe(aperson, MemberRole.owner)
    <Member: aperson@example.com on aardvark@example.com as MemberRole.owner>
    >>> cperson = user_manager.create_address('cperson@example.com')
    >>> mlist.subscribe(cperson, MemberRole.owner)
    <Member: cperson@example.com on aardvark@example.com as MemberRole.owner>
    >>> mlist.subscribe(cperson, MemberRole.moderator)
    <Member: cperson@example.com on aardvark@example.com
             as MemberRole.moderator>

A Person is now both a member and an owner of the mailing list.  C Person is
an owner and a moderator.
::

    >>> for member in sorted(mlist.owners.members, key=sort_key):
    ...     print(member)
    <Member: aperson@example.com on aardvark@example.com as MemberRole.owner>
    <Member: cperson@example.com on aardvark@example.com as MemberRole.owner>

    >>> for member in mlist.moderators.members:
    ...     print(member)
    <Member: cperson@example.com on aardvark@example.com
             as MemberRole.moderator>


All rosters can also be accessed indirectly.
::

    >>> roster = mlist.get_roster(MemberRole.member)
    >>> for member in sorted(roster.members, key=sort_key):
    ...     print(member)
    <Member: aperson@example.com on aardvark@example.com as MemberRole.member>
    <Member: bperson@example.com on aardvark@example.com as MemberRole.member>

    >>> roster = mlist.get_roster(MemberRole.owner)
    >>> for member in sorted(roster.members, key=sort_key):
    ...     print(member)
    <Member: aperson@example.com on aardvark@example.com as MemberRole.owner>
    <Member: cperson@example.com on aardvark@example.com as MemberRole.owner>

    >>> roster = mlist.get_roster(MemberRole.moderator)
    >>> for member in roster.members:
    ...     print(member)
    <Member: cperson@example.com on aardvark@example.com
             as MemberRole.moderator>


Subscribing users
=================

An alternative way of subscribing to a mailing list is as a user with a
preferred address.  This way the user can change their subscription address
just by changing their preferred address.

The user must have a preferred address.

    >>> from mailman.utilities.datetime import now
    >>> user = user_manager.create_user('dperson@example.com', 'Dave Person')
    >>> address = list(user.addresses)[0]
    >>> address.verified_on = now()
    >>> user.preferred_address = address

The preferred address is used in the subscription.

    >>> mlist.subscribe(user)
    <Member: Dave Person <dperson@example.com> on aardvark@example.com
             as MemberRole.member>
    >>> for member in sorted(mlist.members.members, key=sort_key):
    ...     print(member)
    <Member: aperson@example.com on aardvark@example.com as MemberRole.member>
    <Member: bperson@example.com on aardvark@example.com as MemberRole.member>
    <Member: Dave Person <dperson@example.com> on aardvark@example.com
             as MemberRole.member>

If the user's preferred address changes, their subscribed email address also
changes automatically.
::

    >>> new_address = user.register('dave.person@example.com')
    >>> new_address.verified_on = now()
    >>> user.preferred_address = new_address

    >>> for member in sorted(mlist.members.members, key=sort_key):
    ...     print(member)
    <Member: aperson@example.com on aardvark@example.com as MemberRole.member>
    <Member: bperson@example.com on aardvark@example.com as MemberRole.member>
    <Member: dave.person@example.com on aardvark@example.com
             as MemberRole.member>

A user is allowed to explicitly subscribe again with a specific address, even
if this address is their preferred address.

    >>> mlist.subscribe(user.preferred_address)
    <Member: dave.person@example.com
             on aardvark@example.com as MemberRole.member>


.. _`RFC 2369`: http://www.faqs.org/rfcs/rfc2369.html
