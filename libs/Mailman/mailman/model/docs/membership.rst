================
List memberships
================

Users represent people in Mailman, members represent subscriptions.  Users
control email addresses, and rosters are collections of members.  A member
ties a subscribed email address to a role, such as `member`, `administrator`,
or `moderator`.  Even non-members are represented by a roster.

Roster sets are collections of rosters and a mailing list has a single roster
set that contains all its members, regardless of that member's role.

Mailing lists and roster sets have an indirect relationship, through the
roster set's name.  Roster also have names, but are related to roster sets
by a more direct containment relationship.  This is because it is possible to
store mailing list data in a different database than user data.

When we create a mailing list, it starts out with no members, owners,
moderators, administrators, or nonmembers.

    >>> mlist = create_list('ant@example.com')
    >>> dump_list(mlist.members.members)
    *Empty*
    >>> dump_list(mlist.owners.members)
    *Empty*
    >>> dump_list(mlist.moderators.members)
    *Empty*
    >>> dump_list(mlist.administrators.members)
    *Empty*
    >>> dump_list(mlist.nonmembers.members)
    *Empty*


Administrators
==============

A mailing list's administrators are defined as union of the list's owners and
moderators.  We can add new owners or moderators to this list by assigning
roles to users.  First we have to create the user, because there are no users
in the user database yet.

    >>> from mailman.interfaces.usermanager import IUserManager
    >>> from zope.component import getUtility
    >>> user_manager = getUtility(IUserManager)
    >>> user_1 = user_manager.create_user('aperson@example.com', 'Anne Person')
    >>> print(user_1)
    <User "Anne Person" (...) at ...>

We can add Anne as an owner of the mailing list, by creating a member role for
her.

    >>> from mailman.interfaces.member import MemberRole
    >>> address_1 = list(user_1.addresses)[0]
    >>> mlist.subscribe(address_1, MemberRole.owner)
    <Member: Anne Person <aperson@example.com> on
             ant@example.com as MemberRole.owner>
    >>> dump_list(member.address for member in mlist.owners.members)
    Anne Person <aperson@example.com>

Adding Anne as a list owner also makes her an administrator, but does not make
her a moderator.  Nor does it make her a member of the list.

    >>> dump_list(member.address for member in mlist.administrators.members)
    Anne Person <aperson@example.com>
    >>> dump_list(member.address for member in mlist.moderators.members)
    *Empty*
    >>> dump_list(member.address for member in mlist.members.members)
    *Empty*

Bart becomes a moderator of the list.

    >>> user_2 = user_manager.create_user('bperson@example.com', 'Bart Person')
    >>> print(user_2)
    <User "Bart Person" (...) at ...>
    >>> address_2 = list(user_2.addresses)[0]
    >>> mlist.subscribe(address_2, MemberRole.moderator)
    <Member: Bart Person <bperson@example.com>
             on ant@example.com as MemberRole.moderator>
    >>> dump_list(member.address for member in mlist.moderators.members)
    Bart Person <bperson@example.com>

Now, both Anne and Bart are list administrators.
::

    >>> from operator import attrgetter
    >>> def dump_members(roster):
    ...     all_addresses = list(member.address for member in roster)
    ...     sorted_addresses = sorted(all_addresses, key=attrgetter('email'))
    ...     dump_list(sorted_addresses)

    >>> dump_members(mlist.administrators.members)
    Anne Person <aperson@example.com>
    Bart Person <bperson@example.com>


Members
=======

Similarly, list members are born of users being subscribed with the proper
role.

    >>> user_3 = user_manager.create_user(
    ...     'cperson@example.com', 'Cris Person')
    >>> address_3 = list(user_3.addresses)[0]
    >>> member = mlist.subscribe(address_3, MemberRole.member)
    >>> member
    <Member: Cris Person <cperson@example.com>
             on ant@example.com as MemberRole.member>

Cris's user record can also be retrieved from her member record.

    >>> member.user
    <User "Cris Person" (3) at ...>

Cris will be a regular delivery member but not a digest member.

    >>> dump_members(mlist.members.members)
    Cris Person <cperson@example.com>
    >>> dump_members(mlist.regular_members.members)
    Cris Person <cperson@example.com>
    >>> dump_members(mlist.digest_members.addresses)
    *Empty*

It's easy to make the list administrators members of the mailing list too.

    >>> members = []
    >>> for address in mlist.administrators.addresses:
    ...     member = mlist.subscribe(address, MemberRole.member)
    ...     members.append(member)
    >>> dump_list(members, key=attrgetter('address.email'))
    <Member: Anne Person <aperson@example.com> on
             ant@example.com as MemberRole.member>
    <Member: Bart Person <bperson@example.com> on
             ant@example.com as MemberRole.member>
    >>> dump_members(mlist.members.members)
    Anne Person <aperson@example.com>
    Bart Person <bperson@example.com>
    Cris Person <cperson@example.com>
    >>> dump_members(mlist.regular_members.members)
    Anne Person <aperson@example.com>
    Bart Person <bperson@example.com>
    Cris Person <cperson@example.com>
    >>> dump_members(mlist.digest_members.members)
    *Empty*


Nonmembers
==========

Nonmembers are used to represent people who have posted to the mailing list
but are not subscribed to the mailing list.  These may be legitimate users who
have found the mailing list and wish to interact without a direct
subscription, or they may be spammers who should never be allowed to contact
the mailing list.  Because all the same moderation rules can be applied to
nonmembers, we represent them as the same type of object but with a different
role.

    >>> user_6 = user_manager.create_user('fperson@example.com', 'Fred Person')
    >>> address_6 = list(user_6.addresses)[0]
    >>> member_6 = mlist.subscribe(address_6, MemberRole.nonmember)
    >>> member_6
    <Member: Fred Person <fperson@example.com> on ant@example.com
             as MemberRole.nonmember>
    >>> dump_members(mlist.nonmembers.members)
    Fred Person <fperson@example.com>

Nonmembers do not get delivery of any messages.

    >>> dump_members(mlist.members.members)
    Anne Person <aperson@example.com>
    Bart Person <bperson@example.com>
    Cris Person <cperson@example.com>
    >>> dump_members(mlist.regular_members.members)
    Anne Person <aperson@example.com>
    Bart Person <bperson@example.com>
    Cris Person <cperson@example.com>
    >>> dump_members(mlist.digest_members.members)
    *Empty*


Finding members
===============

You can find the ``IMember`` object that is a member of a roster for a given
text email address by using the ``IRoster.get_member()`` method.

    >>> mlist.owners.get_member('aperson@example.com')
    <Member: Anne Person <aperson@example.com> on
             ant@example.com as MemberRole.owner>
    >>> mlist.administrators.get_member('aperson@example.com')
    <Member: Anne Person <aperson@example.com> on
             ant@example.com as MemberRole.owner>
    >>> mlist.members.get_member('aperson@example.com')
    <Member: Anne Person <aperson@example.com> on
             ant@example.com as MemberRole.member>
    >>> mlist.nonmembers.get_member('fperson@example.com')
    <Member: Fred Person <fperson@example.com> on
             ant@example.com as MemberRole.nonmember>

However, if the address is not subscribed with the appropriate role, then None
is returned.

    >>> print(mlist.administrators.get_member('zperson@example.com'))
    None
    >>> print(mlist.moderators.get_member('aperson@example.com'))
    None
    >>> print(mlist.members.get_member('zperson@example.com'))
    None
    >>> print(mlist.nonmembers.get_member('aperson@example.com'))
    None


All subscribers
===============

There is also a roster containing all the subscribers of a mailing list,
regardless of their role.

    >>> def sortkey(member):
    ...     return (member.address.email, member.role.value)
    >>> for member in sorted(mlist.subscribers.members, key=sortkey):
    ...     print(member.address.email, member.role)
    aperson@example.com MemberRole.member
    aperson@example.com MemberRole.owner
    bperson@example.com MemberRole.member
    bperson@example.com MemberRole.moderator
    cperson@example.com MemberRole.member
    fperson@example.com MemberRole.nonmember


Subscriber type
===============

Members can be subscribed to a mailing list either via an explicit address, or
indirectly through a user's preferred address.  Sometimes you want to know
which one it is.

Herb subscribes to the mailing list via an explicit address.

    >>> herb = user_manager.create_address(
    ...     'hperson@example.com', 'Herb Person')
    >>> herb_member = mlist.subscribe(herb)

Iris subscribes to the mailing list via her preferred address.

    >>> iris = user_manager.make_user(
    ...     'iperson@example.com', 'Iris Person')
    >>> preferred = list(iris.addresses)[0]
    >>> from mailman.utilities.datetime import now
    >>> preferred.verified_on = now()
    >>> iris.preferred_address = preferred
    >>> iris_member = mlist.subscribe(iris)

When we need to know which way a member is subscribed, we can look at the this
attribute.

    >>> herb_member.subscriber
    <Address: Herb Person <hperson@example.com> [not verified] at ...>
    >>> iris_member.subscriber
    <User "Iris Person" (5) at ...>


Moderation actions
==================

All members of any role have a *moderation action* which specifies how
postings from that member are handled.  By default, owners and moderators are
automatically accepted for posting to the mailing list.

    >>> for member in sorted(mlist.administrators.members,
    ...                      key=attrgetter('address.email')):
    ...     print(member.address.email, member.role, member.moderation_action)
    aperson@example.com MemberRole.owner     Action.accept
    bperson@example.com MemberRole.moderator Action.accept

By default, members and nonmembers have their action set to None, meaning that
the mailing list's ``default_member_action`` or ``default_nonmember_action``
will be used.

    >>> for member in sorted(mlist.members.members,
    ...                      key=attrgetter('address.email')):
    ...     print(member.address.email, member.role, member.moderation_action)
    aperson@example.com MemberRole.member None
    bperson@example.com MemberRole.member None
    cperson@example.com MemberRole.member None
    hperson@example.com MemberRole.member None
    iperson@example.com MemberRole.member None

    >>> for member in mlist.nonmembers.members:
    ...     print(member.address.email, member.role, member.moderation_action)
    fperson@example.com MemberRole.nonmember None

The mailing list's default action for members is *deferred*, which specifies
that the posting should go through the normal moderation checks. Its default
action for nonmembers is to hold for moderator approval.


Changing subscriptions
======================

When a user is subscribed to a mailing list via a specific address they
control (as opposed to being subscribed with their preferred address), they
can change their delivery address by setting the appropriate parameter.  Note
though that the address they're changing to must be verified.

    >>> bee = create_list('bee@example.com')
    >>> gwen = user_manager.create_user('gwen@example.com')
    >>> gwen_address = list(gwen.addresses)[0]
    >>> gwen_member = bee.subscribe(gwen_address)
    >>> for m in bee.members.members:
    ...     print(m.member_id.int, m.mailing_list.list_id, m.address.email)
    9 bee.example.com gwen@example.com

Gwen gets a email address.

    >>> new_address = gwen.register('gperson@example.com')

Gwen verifies her email address, and updates her membership.

    >>> from mailman.utilities.datetime import now
    >>> new_address.verified_on = now()
    >>> gwen_member.address = new_address

Now her membership reflects the new address.

    >>> for m in bee.members.members:
    ...     print(m.member_id.int, m.mailing_list.list_id, m.address.email)
    9 bee.example.com gperson@example.com


Events
======

An event is triggered when a new member is subscribed to a mailing list.
::

    >>> from mailman.testing.helpers import event_subscribers
    >>> def handle_event(event):
    ...     print(event)

    >>> cat = create_list('cat@example.com')
    >>> herb = user_manager.create_address('herb@example.com')
    >>> with event_subscribers(handle_event):
    ...     member = cat.subscribe(herb)
    herb@example.com joined cat.example.com

An event is triggered when a member is unsubscribed from a mailing list.

    >>> with event_subscribers(handle_event):
    ...     member.unsubscribe()
    herb@example.com left cat.example.com
