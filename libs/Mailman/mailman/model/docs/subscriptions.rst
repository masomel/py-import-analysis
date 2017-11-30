===============
 Subscriptions
===============

When a user wants to join a mailing list, they must register and verify their
email address.  Then depending on how the mailing list is configured, they may
need to confirm their subscription and have it approved by the list moderator.
The ``ISubscriptionManager`` interface manages this work flow.

    >>> from mailman.interfaces.subscriptions import ISubscriptionManager

To begin, adapt a mailing list to an ``ISubscriptionManager``.  This is a
named interface because the same interface manages both subscriptions and
unsubscriptions.

    >>> mlist = create_list('ant@example.com')
    >>> manager = ISubscriptionManager(mlist)

Either addresses or users with a preferred address can be registered.

    >>> from mailman.interfaces.usermanager import IUserManager
    >>> from zope.component import getUtility
    >>> anne = getUtility(IUserManager).create_address(
    ...     'anne@example.com', 'Anne Person')


Subscribing an email address
============================

The subscription process requires that the email address be verified.  It may
also require confirmation or moderator approval depending on the mailing
list's subscription policy.  For example, an open subscription policy does not
require confirmation or approval, but the email address must still be
verified, and the process will pause until these steps are completed.

    >>> from mailman.interfaces.mailinglist import SubscriptionPolicy
    >>> mlist.subscription_policy = SubscriptionPolicy.open

Anne attempts to join the mailing list.  A unique token is created which
represents this work flow.

    >>> token, token_owner, member = manager.register(anne)

Because her email address has not yet been verified, she has not yet become a
member of the mailing list.

    >>> print(member)
    None
    >>> print(mlist.members.get_member('anne@example.com'))
    None

Once she verifies her email address, she will become a member of the mailing
list.  When the subscription policy requires confirmation, the verification
process implies that she also confirms her wish to join the mailing list.

    >>> token, token_owner, member = manager.confirm(token)
    >>> member
    <Member: Anne Person <anne@example.com> on ant@example.com
        as MemberRole.member>
    >>> mlist.members.get_member('anne@example.com')
    <Member: Anne Person <anne@example.com> on ant@example.com
        as MemberRole.member>


Subscribing a user
==================

Users can also register, but they must have a preferred address.  The mailing
list will deliver messages to this preferred address.

    >>> bart = getUtility(IUserManager).make_user(
    ...     'bart@example.com', 'Bart Person')

Bart verifies his address and makes it his preferred address.

    >>> from mailman.utilities.datetime import now
    >>> preferred = list(bart.addresses)[0]
    >>> preferred.verified_on = now()
    >>> bart.preferred_address = preferred

The mailing list's subscription policy does not require Bart to confirm his
subscription, but the moderate does want to approve all subscriptions.

    >>> mlist.subscription_policy = SubscriptionPolicy.moderate

Now when Bart registers as a user for the mailing list, a token will still be
generated, but this is only used by the moderator.  At first, Bart is not
subscribed to the mailing list.

    >>> token, token_owner, member = manager.register(bart)
    >>> print(member)
    None
    >>> print(mlist.members.get_member('bart@example.com'))
    None

When the moderator confirms Bart's subscription, he joins the mailing list.

    >>> token, token_owner, member = manager.confirm(token)
    >>> member
    <Member: Bart Person <bart@example.com> on ant@example.com
        as MemberRole.member>
    >>> mlist.members.get_member('bart@example.com')
    <Member: Bart Person <bart@example.com> on ant@example.com
        as MemberRole.member>


Unsubscribing
=============

Similarly, unsubscribing a user depends on the mailing list's unsubscription
policy.  Of course, since the address or user is already subscribed, implying
that their email address is already verified, that step is not required.  To
begin with unsubscribing, you need to adapt the mailing list to the same
interface, but with a different name.

    >>> manager = ISubscriptionManager(mlist)

If the mailing list's unsubscription policy is open, unregistering the
subscription takes effect immediately.

    >>> mlist.unsubscription_policy = SubscriptionPolicy.open
    >>> token, token_owner, member = manager.unregister(anne)
    >>> print(mlist.members.get_member('anne@example.com'))
    None

Usually though, the member must confirm their unsubscription request, to
prevent an attacker from unsubscribing them from the list without their
knowledge.

    >>> mlist.unsubscription_policy = SubscriptionPolicy.confirm
    >>> token, token_owner, member = manager.unregister(bart)

Bart hasn't confirmed yet, so he's still a member of the list.

    >>> mlist.members.get_member('bart@example.com')
    <Member: Bart Person <bart@example.com> on ant@example.com
        as MemberRole.member>

Once Bart confirms, he's unsubscribed from the mailing list.

    >>> token, token_owner, member = manager.confirm(token)
    >>> print(mlist.members.get_member('bart@example.com'))
    None


Subscription services
=====================

The ``ISubscriptionService`` utility provides higher level convenience methods
useful for searching, retrieving, iterating, and removing memberships across
all mailing lists on the system.

    >>> from mailman.interfaces.subscriptions import ISubscriptionService
    >>> service = getUtility(ISubscriptionService)

You can use the service to get all members of all mailing lists, for any
membership role.  At first, there are no memberships.

    >>> service.get_members()
    []
    >>> sum(1 for member in service)
    0
    >>> from uuid import UUID
    >>> print(service.get_member(UUID(int=801)))
    None


Listing members
===============

When there are some members, of any role on any mailing list, they can be
retrieved through the subscription service.

    >>> from mailman.app.lifecycle import create_list
    >>> ant = mlist
    >>> bee = create_list('bee@example.com')
    >>> cat = create_list('cat@example.com')

Some people become members.

    >>> from mailman.interfaces.member import MemberRole
    >>> from mailman.testing.helpers import subscribe
    >>> anne_1 = subscribe(ant, 'Anne')
    >>> anne_2 = subscribe(ant, 'Anne', MemberRole.owner)
    >>> bart_1 = subscribe(ant, 'Bart', MemberRole.moderator)
    >>> bart_2 = subscribe(bee, 'Bart', MemberRole.owner)
    >>> anne_3 = subscribe(cat, 'Anne', email='anne@example.com')
    >>> cris_1 = subscribe(cat, 'Cris')

The service can be used to iterate over them.

    >>> for member in service.get_members():
    ...     print(member)
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.owner>
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.moderator>
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Bart Person <bperson@example.com>
        on bee@example.com as MemberRole.owner>
    <Member: Anne Person <anne@example.com>
        on cat@example.com as MemberRole.member>
    <Member: Cris Person <cperson@example.com>
        on cat@example.com as MemberRole.member>

The service can also be used to get the information about a single member.

    >>> print(service.get_member(bart_2.member_id))
    <Member: Bart Person <bperson@example.com>
        on bee@example.com as MemberRole.owner>

There is an iteration shorthand for getting all the members.

    >>> for member in service:
    ...     print(member)
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.owner>
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.moderator>
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Bart Person <bperson@example.com>
        on bee@example.com as MemberRole.owner>
    <Member: Anne Person <anne@example.com>
        on cat@example.com as MemberRole.member>
    <Member: Cris Person <cperson@example.com>
        on cat@example.com as MemberRole.member>


Searching for members
=====================

The subscription service can be used to find memberships based on specific
search criteria.  For example, we can find all the mailing lists that Anne is
a member of with her ``aperson@example.com`` address.

    >>> for member in service.find_members('aperson@example.com'):
    ...     print(member)
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.owner>

There may be no matching memberships.

    >>> list(service.find_members('dave@example.com'))
    []

The address may contain asterisks, which will be interpreted as a wildcard in
the search pattern.

    >>> for member in service.find_members('*person*'):
    ...     print(member)
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.owner>
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.moderator>
    <Member: Bart Person <bperson@example.com>
        on bee@example.com as MemberRole.owner>
    <Member: Cris Person <cperson@example.com>
        on cat@example.com as MemberRole.member>

Memberships can also be searched for by user id.

    >>> for member in service.find_members(anne_1.user.user_id):
    ...     print(member)
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.owner>

You can find all the memberships for a specific mailing list.

    >>> for member in service.find_members(list_id='ant.example.com'):
    ...     print(member)
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.owner>
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.moderator>

You can find all the memberships for an address on a specific mailing list,
but you have to give it the list id, not the fqdn listname since the former is
stable but the latter could change if the list is moved.

    >>> for member in service.find_members(
    ...         'bperson@example.com', 'ant.example.com'):
    ...     print(member)
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.moderator>

You can find all the memberships for an address with a specific role.

    >>> for member in service.find_members(
    ...         list_id='ant.example.com', role=MemberRole.owner):
    ...     print(member)
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.owner>

You can also find a specific membership by all three criteria.

    >>> for member in service.find_members(
    ...         'bperson@example.com', 'bee.example.com', MemberRole.owner):
    ...     print(member)
    <Member: Bart Person <bperson@example.com>
        on bee@example.com as MemberRole.owner>


Finding a single member
=======================

If you expect only zero or one member to match your criteria, you can use a
the more efficient ``find_member()`` method.  This takes exactly the same
criteria as ``find_members()``.

There may be no matching members.

    >>> print(service.find_member('dave@example.com'))
    None

But if there is exactly one membership, it is returned.

    >>> service.find_member('bperson@example.com', 'ant.example.com')
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.moderator>


Removing members
================

Members can be removed via this service.

    >>> len(service.get_members())
    6
    >>> service.leave('cat.example.com', 'cperson@example.com')
    >>> len(service.get_members())
    5
    >>> for member in service:
    ...     print(member)
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.owner>
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.moderator>
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Bart Person <bperson@example.com>
        on bee@example.com as MemberRole.owner>
    <Member: Anne Person <anne@example.com>
        on cat@example.com as MemberRole.member>


Mass Removal
============

The subscription service can be used to perform mass removals.  You are
required to pass the list id of the respective mailing list and a list
of email addresses to be removed.

    >>> bart_2 = subscribe(ant, 'Bart')
    >>> cris_2 = subscribe(ant, 'Cris')
    >>> for member in service:
    ...     print(member)
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.owner>
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.moderator>
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Cris Person <cperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Bart Person <bperson@example.com>
        on bee@example.com as MemberRole.owner>
    <Member: Anne Person <anne@example.com>
        on cat@example.com as MemberRole.member>

There are now two more memberships.

    >>> len(service.get_members())
    7

But this address is not subscribed to any mailing list.

    >>> print(service.find_member('bogus@example.com'))
    None

We can unsubscribe some addresses from the ant mailing list.  Note that even
though Anne is subscribed several times, only her ant membership with role
``member`` will be removed.

    >>> success, fail = service.unsubscribe_members(
    ...     'ant.example.com', [
    ...         'aperson@example.com',
    ...         'cperson@example.com',
    ...         'bogus@example.com',
    ...         ])

There were some successes...

    >>> dump_list(success)
    aperson@example.com
    cperson@example.com

...and some failures.

    >>> dump_list(fail)
    bogus@example.com

And now there are 5 memberships again.

    >>> for member in service:
    ...     print(member)
    <Member: Anne Person <aperson@example.com>
        on ant@example.com as MemberRole.owner>
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.moderator>
    <Member: Bart Person <bperson@example.com>
        on ant@example.com as MemberRole.member>
    <Member: Bart Person <bperson@example.com>
        on bee@example.com as MemberRole.owner>
    <Member: Anne Person <anne@example.com>
        on cat@example.com as MemberRole.member>
    >>> len(service.get_members())
    5
