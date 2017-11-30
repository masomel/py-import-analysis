==========
Membership
==========

The REST API can be used to subscribe and unsubscribe users to mailing lists.
A subscribed user is called a *member*.  There is a top level collection that
returns all the members of all known mailing lists.

There are no mailing lists and no members yet.

    >>> dump_json('http://localhost:9001/3.0/members')
    http_etag: "..."
    start: 0
    total_size: 0

We create a mailing list, which starts out with no members.
::

    >>> bee = create_list('bee@example.com')
    >>> transaction.commit()

    >>> dump_json('http://localhost:9001/3.0/members')
    http_etag: "..."
    start: 0
    total_size: 0


Subscribers
===========

After Bart subscribes to the mailing list, his subscription is available via
the REST interface.
::

    >>> from mailman.interfaces.member import MemberRole
    >>> from mailman.interfaces.usermanager import IUserManager
    >>> from zope.component import getUtility
    >>> user_manager = getUtility(IUserManager)

    >>> from mailman.testing.helpers import subscribe
    >>> subscribe(bee, 'Bart')
    <Member: Bart Person <bperson@example.com> on bee@example.com
             as MemberRole.member>

    >>> dump_json('http://localhost:9001/3.0/members')
    entry 0:
        address: http://localhost:9001/3.0/addresses/bperson@example.com
        delivery_mode: regular
        email: bperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 1
        role: member
        self_link: http://localhost:9001/3.0/members/1
        user: http://localhost:9001/3.0/users/1
    http_etag: "..."
    start: 0
    total_size: 1

Bart's specific membership can be accessed directly:

    >>> dump_json('http://localhost:9001/3.0/members/1')
    address: http://localhost:9001/3.0/addresses/bperson@example.com
    delivery_mode: regular
    email: bperson@example.com
    http_etag: ...
    list_id: bee.example.com
    member_id: 1
    role: member
    self_link: http://localhost:9001/3.0/members/1
    user: http://localhost:9001/3.0/users/1

When Cris also joins the mailing list, her subscription is also available via
the REST interface.
::

    >>> subscribe(bee, 'Cris')
    <Member: Cris Person <cperson@example.com> on bee@example.com
             as MemberRole.member>

    >>> dump_json('http://localhost:9001/3.0/members')
    entry 0:
        address: http://localhost:9001/3.0/addresses/bperson@example.com
        delivery_mode: regular
        email: bperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 1
        role: member
        self_link: http://localhost:9001/3.0/members/1
        user: http://localhost:9001/3.0/users/1
    entry 1:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 2
        role: member
        self_link: http://localhost:9001/3.0/members/2
        user: http://localhost:9001/3.0/users/2
    http_etag: "..."
    start: 0
    total_size: 2

The subscribed members are returned in alphabetical order, so when Anna
subscribes, she is returned first.
::

    >>> subscribe(bee, 'Anna')
    <Member: Anna Person <aperson@example.com> on bee@example.com
             as MemberRole.member>

    >>> dump_json('http://localhost:9001/3.0/members')
    entry 0:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 3
        role: member
        self_link: http://localhost:9001/3.0/members/3
        user: http://localhost:9001/3.0/users/3
    entry 1:
        address: http://localhost:9001/3.0/addresses/bperson@example.com
        delivery_mode: regular
        email: bperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 1
        role: member
        self_link: http://localhost:9001/3.0/members/1
        user: http://localhost:9001/3.0/users/1
    entry 2:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 2
        role: member
        self_link: http://localhost:9001/3.0/members/2
        user: http://localhost:9001/3.0/users/2
    http_etag: "..."
    start: 0
    total_size: 3

Subscriptions are also returned alphabetically by mailing list posting
address.  Anna and Cris subscribe to this new mailing list.
::

    >>> ant = create_list('ant@example.com')
    >>> subscribe(ant, 'Anna')
    <Member: Anna Person <aperson@example.com> on ant@example.com
             as MemberRole.member>
    >>> subscribe(ant, 'Cris')
    <Member: Cris Person <cperson@example.com> on ant@example.com
             as MemberRole.member>

User ids are different than member ids.

    >>> dump_json('http://localhost:9001/3.0/members')
    entry 0:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 4
        role: member
        self_link: http://localhost:9001/3.0/members/4
        user: http://localhost:9001/3.0/users/3
    entry 1:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 5
        role: member
        self_link: http://localhost:9001/3.0/members/5
        user: http://localhost:9001/3.0/users/2
    entry 2:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 3
        role: member
        self_link: http://localhost:9001/3.0/members/3
        user: http://localhost:9001/3.0/users/3
    entry 3:
        address: http://localhost:9001/3.0/addresses/bperson@example.com
        delivery_mode: regular
        email: bperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 1
        role: member
        self_link: http://localhost:9001/3.0/members/1
        user: http://localhost:9001/3.0/users/1
    entry 4:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 2
        role: member
        self_link: http://localhost:9001/3.0/members/2
        user: http://localhost:9001/3.0/users/2
    http_etag: "..."
    start: 0
    total_size: 5

We can also get just the members of a single mailing list.

    >>> dump_json(
    ...     'http://localhost:9001/3.0/lists/ant@example.com/roster/member')
    entry 0:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 4
        role: member
        self_link: http://localhost:9001/3.0/members/4
        user: http://localhost:9001/3.0/users/3
    entry 1:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 5
        role: member
        self_link: http://localhost:9001/3.0/members/5
        user: http://localhost:9001/3.0/users/2
    http_etag: ...
    start: 0
    total_size: 2


Paginating over member records
------------------------------

Instead of returning all the member records at once, it's possible to return
them in pages by adding the GET parameters ``count`` and ``page`` to the
request URI.  Page 1 is the first page and ``count`` defines the size of the
page.

    >>> dump_json(
    ...     'http://localhost:9001/3.0/lists/ant@example.com/roster/member'
    ...     '?count=1&page=1')
    entry 0:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 4
        role: member
        self_link: http://localhost:9001/3.0/members/4
        user: http://localhost:9001/3.0/users/3
    http_etag: ...
    start: 0
    total_size: 2

This works with members of a single list as well as with all members.

    >>> dump_json(
    ...     'http://localhost:9001/3.0/members?count=1&page=1')
    entry 0:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 4
        role: member
        self_link: http://localhost:9001/3.0/members/4
        user: http://localhost:9001/3.0/users/3
    http_etag: ...
    start: 0
    total_size: 5


Owners and moderators
=====================

Mailing list owners and moderators also show up in the REST API.  Cris becomes
an owner of the `ant` mailing list and Dave becomes a moderator of the `bee`
mailing list.
::

    >>> dump_json('http://localhost:9001/3.0/members', {
    ...           'list_id': 'ant.example.com',
    ...           'subscriber': 'dperson@example.com',
    ...           'role': 'moderator',
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/members/6
    server: ...
    status: 201

    >>> dump_json('http://localhost:9001/3.0/members', {
    ...           'list_id': 'bee.example.com',
    ...           'subscriber': 'cperson@example.com',
    ...           'role': 'owner',
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/members/7
    server: ...
    status: 201

    >>> dump_json('http://localhost:9001/3.0/members')
    entry 0:
        address: http://localhost:9001/3.0/addresses/dperson@example.com
        delivery_mode: regular
        email: dperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 6
        moderation_action: accept
        role: moderator
        self_link: http://localhost:9001/3.0/members/6
        user: http://localhost:9001/3.0/users/4
    entry 1:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 4
        role: member
        self_link: http://localhost:9001/3.0/members/4
        user: http://localhost:9001/3.0/users/3
    entry 2:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 5
        role: member
        self_link: http://localhost:9001/3.0/members/5
        user: http://localhost:9001/3.0/users/2
    entry 3:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 7
        moderation_action: accept
        role: owner
        self_link: http://localhost:9001/3.0/members/7
        user: http://localhost:9001/3.0/users/2
    entry 4:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 3
        role: member
        self_link: http://localhost:9001/3.0/members/3
        user: http://localhost:9001/3.0/users/3
    entry 5:
        address: http://localhost:9001/3.0/addresses/bperson@example.com
        delivery_mode: regular
        email: bperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 1
        role: member
        self_link: http://localhost:9001/3.0/members/1
        user: http://localhost:9001/3.0/users/1
    entry 6:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 2
        role: member
        self_link: http://localhost:9001/3.0/members/2
        user: http://localhost:9001/3.0/users/2
    http_etag: "..."
    start: 0
    total_size: 7

We can access all the owners of a list.

    >>> dump_json(
    ...     'http://localhost:9001/3.0/lists/bee@example.com/roster/owner')
    entry 0:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 7
        moderation_action: accept
        role: owner
        self_link: http://localhost:9001/3.0/members/7
        user: http://localhost:9001/3.0/users/2
    http_etag: ...
    start: 0
    total_size: 1


Finding members
===============

A specific member can always be referenced by their role and address.

    >>> dump_json('http://localhost:9001/3.0/lists/'
    ...           'bee@example.com/owner/cperson@example.com')
    address: http://localhost:9001/3.0/addresses/cperson@example.com
    delivery_mode: regular
    email: cperson@example.com
    http_etag: ...
    list_id: bee.example.com
    member_id: 7
    moderation_action: accept
    role: owner
    self_link: http://localhost:9001/3.0/members/7
    user: http://localhost:9001/3.0/users/2

You can find a specific member based on several different criteria.  For
example, we can search for all the memberships of a particular address.

    >>> dump_json('http://localhost:9001/3.0/members/find', {
    ...           'subscriber': 'aperson@example.com',
    ...           })
    entry 0:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 4
        role: member
        self_link: http://localhost:9001/3.0/members/4
        user: http://localhost:9001/3.0/users/3
    entry 1:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 3
        role: member
        self_link: http://localhost:9001/3.0/members/3
        user: http://localhost:9001/3.0/users/3
    http_etag: ...
    start: 0
    total_size: 2

Or, we can find all the memberships for a particular mailing list.

    >>> dump_json('http://localhost:9001/3.0/members/find', {
    ...           'list_id': 'bee.example.com',
    ...           })
    entry 0:
        address: http://localhost:9001/3.0/addresses/aperson@example.com
        delivery_mode: regular
        email: aperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 3
        role: member
        self_link: http://localhost:9001/3.0/members/3
        user: http://localhost:9001/3.0/users/3
    entry 1:
        address: http://localhost:9001/3.0/addresses/bperson@example.com
        delivery_mode: regular
        email: bperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 1
        role: member
        self_link: http://localhost:9001/3.0/members/1
        user: http://localhost:9001/3.0/users/1
    entry 2:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 2
        role: member
        self_link: http://localhost:9001/3.0/members/2
        user: http://localhost:9001/3.0/users/2
    entry 3:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 7
        moderation_action: accept
        role: owner
        self_link: http://localhost:9001/3.0/members/7
        user: http://localhost:9001/3.0/users/2
    http_etag: "..."
    start: 0
    total_size: 4

Or, we can find all the memberships for an address on a particular mailing
list.

    >>> dump_json('http://localhost:9001/3.0/members/find', {
    ...           'subscriber': 'cperson@example.com',
    ...           'list_id': 'bee.example.com',
    ...           })
    entry 0:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 2
        role: member
        self_link: http://localhost:9001/3.0/members/2
        user: http://localhost:9001/3.0/users/2
    entry 1:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 7
        moderation_action: accept
        role: owner
        self_link: http://localhost:9001/3.0/members/7
        user: http://localhost:9001/3.0/users/2
    http_etag: ...
    start: 0
    total_size: 2

Or, we can find all the memberships for an address with a specific role.

    >>> dump_json('http://localhost:9001/3.0/members/find', {
    ...           'subscriber': 'cperson@example.com',
    ...           'role': 'member',
    ...           })
    entry 0:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 5
        role: member
        self_link: http://localhost:9001/3.0/members/5
        user: http://localhost:9001/3.0/users/2
    entry 1:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 2
        role: member
        self_link: http://localhost:9001/3.0/members/2
        user: http://localhost:9001/3.0/users/2
    http_etag: ...
    start: 0
    total_size: 2

Finally, we can search for a specific member given all three criteria.

    >>> dump_json('http://localhost:9001/3.0/members/find', {
    ...           'subscriber': 'cperson@example.com',
    ...           'list_id': 'bee.example.com',
    ...           'role': 'member',
    ...           })
    entry 0:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 2
        role: member
        self_link: http://localhost:9001/3.0/members/2
        user: http://localhost:9001/3.0/users/2
    http_etag: ...
    start: 0
    total_size: 1

Search can also be performed using HTTP GET queries.

    >>> dump_json('http://localhost:9001/3.0/members/find'
    ...           '?subscriber=cperson@example.com'
    ...           '&list_id=bee.example.com'
    ...           '&role=member'
    ...           )
    entry 0:
        address: http://localhost:9001/3.0/addresses/cperson@example.com
        delivery_mode: regular
        email: cperson@example.com
        http_etag: ...
        list_id: bee.example.com
        member_id: 2
        role: member
        self_link: http://localhost:9001/3.0/members/2
        user: http://localhost:9001/3.0/users/2
    http_etag: ...
    start: 0
    total_size: 1


Joining a mailing list
======================

A user can be subscribed to a mailing list via the REST API, either by a
specific address, or more generally by their preferred address.  A subscribed
user is called a member.

Elly subscribes to the `ant` mailing list.  Since her email address is not yet
known to Mailman, a user is created for her.  By default, she gets a regular
delivery.

By pre-verifying her subscription, we don't require Elly to verify that her
email address is valid.  By pre-confirming her subscription too, no
confirmation email will be sent.  Pre-approval means that the list moderator
won't have to approve her subscription request.

    >>> dump_json('http://localhost:9001/3.0/members', {
    ...           'list_id': 'ant.example.com',
    ...           'subscriber': 'eperson@example.com',
    ...           'display_name': 'Elly Person',
    ...           'pre_verified': True,
    ...           'pre_confirmed': True,
    ...           'pre_approved': True,
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/members/8
    server: ...
    status: 201

Elly is now a known user, and a member of the mailing list.
::

    >>> elly = user_manager.get_user('eperson@example.com')
    >>> elly
    <User "Elly Person" (...) at ...>

    >>> set(member.list_id for member in elly.memberships.members)
    {'ant.example.com'}

    >>> dump_json('http://localhost:9001/3.0/members')
    entry 0:
    ...
    entry 3:
        address: http://localhost:9001/3.0/addresses/eperson@example.com
        delivery_mode: regular
        email: eperson@example.com
        http_etag: ...
        list_id: ant.example.com
        member_id: 8
        role: member
        self_link: http://localhost:9001/3.0/members/8
        user: http://localhost:9001/3.0/users/5
    ...

Gwen is a user with a preferred address.  She subscribes to the `ant` mailing
list with her preferred address.
::

    >>> from mailman.utilities.datetime import now
    >>> gwen = user_manager.create_user('gwen@example.com', 'Gwen Person')
    >>> preferred = list(gwen.addresses)[0]
    >>> preferred.verified_on = now()
    >>> gwen.preferred_address = preferred

    # Note that we must extract the user id before we commit the transaction.
    # This is because accessing the .user_id attribute will lock the database
    # in the testing process, breaking the REST queue process.  Also, the
    # user_id is a UUID internally, but an integer (represented as a string)
    # is required by the REST API.
    >>> user_id = gwen.user_id.int
    >>> transaction.commit()

    >>> dump_json('http://localhost:9001/3.0/members', {
    ...     'list_id': 'ant.example.com',
    ...     'subscriber': user_id,
    ...     'pre_verified': True,
    ...     'pre_confirmed': True,
    ...     'pre_approved': True,
    ...     })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/members/9
    server: ...
    status: 201

    >>> dump_json('http://localhost:9001/3.0/members')
    entry 0:
    ...
    entry 4:
        address: http://localhost:9001/3.0/addresses/gwen@example.com
        delivery_mode: regular
        email: gwen@example.com
        http_etag: "..."
        list_id: ant.example.com
        member_id: 9
        role: member
        self_link: http://localhost:9001/3.0/members/9
        user: http://localhost:9001/3.0/users/6
    ...
    total_size: 9

When Gwen changes her preferred address, her subscription automatically tracks
the new address.
::

    >>> new_preferred = gwen.register('gwen.person@example.com')
    >>> new_preferred.verified_on = now()
    >>> gwen.preferred_address = new_preferred
    >>> transaction.commit()

    >>> dump_json('http://localhost:9001/3.0/members')
    entry 0:
    ...
    entry 4:
        address: http://localhost:9001/3.0/addresses/gwen.person@example.com
        delivery_mode: regular
        email: gwen.person@example.com
        http_etag: "..."
        list_id: ant.example.com
        member_id: 9
        role: member
        self_link: http://localhost:9001/3.0/members/9
        user: http://localhost:9001/3.0/users/6
    ...
    total_size: 9


Leaving a mailing list
======================

Elly decides she does not want to be a member of the mailing list after all,
so she leaves from the mailing list.
::

    # Ensure our previous reads don't keep the database lock.
    >>> transaction.abort()
    >>> dump_json('http://localhost:9001/3.0/members/8',
    ...           method='DELETE')
    content-length: 0
    ...
    status: 204

Elly is no longer a member of the mailing list.

    >>> set(member.mailing_list for member in elly.memberships.members)
    set()


Changing delivery address
=========================

As shown above, Gwen is subscribed to a mailing list with her preferred email
address.  If she changes her preferred address, this automatically changes the
address she will receive deliveries at for all such memberships.

However, when Herb subscribes to a couple of mailing lists with explicit
addresses, he must change each subscription explicitly.

Herb controls multiple email addresses.  All of these addresses are verified.

    >>> herb = user_manager.create_user('herb@example.com', 'Herb Person')
    >>> herb_1 = list(herb.addresses)[0]
    >>> herb_2 = herb.register('hperson@example.com')
    >>> herb_3 = herb.register('herb.person@example.com')
    >>> for address in herb.addresses:
    ...     address.verified_on = now()

Herb subscribes to both the `ant` and `bee` mailing lists with one of his
addresses.

    >>> ant.subscribe(herb_1)
    <Member: Herb Person <herb@example.com> on
             ant@example.com as MemberRole.member>
    >>> bee.subscribe(herb_1)
    <Member: Herb Person <herb@example.com> on
             bee@example.com as MemberRole.member>
    >>> transaction.commit()
    >>> dump_json('http://localhost:9001/3.0/members')
    entry 0:
    ...
    entry 4:
        address: http://localhost:9001/3.0/addresses/herb@example.com
        delivery_mode: regular
        email: herb@example.com
        http_etag: "..."
        list_id: ant.example.com
        member_id: 10
        role: member
        self_link: http://localhost:9001/3.0/members/10
        user: http://localhost:9001/3.0/users/7
    ...
    entry 9:
        address: http://localhost:9001/3.0/addresses/herb@example.com
        delivery_mode: regular
        email: herb@example.com
        http_etag: "..."
        list_id: bee.example.com
        member_id: 11
        role: member
        self_link: http://localhost:9001/3.0/members/11
        user: http://localhost:9001/3.0/users/7
    http_etag: "..."
    start: 0
    total_size: 10

In order to change all of his subscriptions to use a different email address,
Herb must iterate through his memberships explicitly.

    >>> from mailman.testing.helpers import call_api
    >>> content, response = call_api('http://localhost:9001/3.0/addresses/'
    ...                              'herb@example.com/memberships')
    >>> memberships = [entry['self_link'] for entry in content['entries']]
    >>> for url in sorted(memberships):
    ...     print(url)
    http://localhost:9001/3.0/members/10
    http://localhost:9001/3.0/members/11

For each membership resource, the subscription address is changed by PATCH'ing
the `address` attribute.

    >>> dump_json('http://localhost:9001/3.0/members/10', {
    ...           'address': 'hperson@example.com',
    ...           }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/members/11', {
    ...           'address': 'hperson@example.com',
    ...           }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

Herb's memberships with the old address are gone.

    >>> dump_json('http://localhost:9001/3.0/addresses/'
    ...           'herb@example.com/memberships')
    http_etag: "..."
    start: 0
    total_size: 0

Herb's memberships have been updated with his new email address.  Of course,
his membership ids have not changed.

    >>> dump_json('http://localhost:9001/3.0/addresses/'
    ...           'hperson@example.com/memberships')
    entry 0:
        address: http://localhost:9001/3.0/addresses/hperson@example.com
        delivery_mode: regular
        email: hperson@example.com
        http_etag: "..."
        list_id: ant.example.com
        member_id: 10
        role: member
        self_link: http://localhost:9001/3.0/members/10
        user: http://localhost:9001/3.0/users/7
    entry 1:
        address: http://localhost:9001/3.0/addresses/hperson@example.com
        delivery_mode: regular
        email: hperson@example.com
        http_etag: "..."
        list_id: bee.example.com
        member_id: 11
        role: member
        self_link: http://localhost:9001/3.0/members/11
        user: http://localhost:9001/3.0/users/7
    http_etag: "..."
    start: 0
    total_size: 2

When changing his subscription address, Herb may also decide to change his
mode of delivery.
::

    >>> dump_json('http://localhost:9001/3.0/members/11', {
    ...           'address': 'herb@example.com',
    ...           'delivery_mode': 'mime_digests',
    ...           }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/addresses/'
    ...           'herb@example.com/memberships')
    entry 0:
        address: http://localhost:9001/3.0/addresses/herb@example.com
        delivery_mode: mime_digests
        email: herb@example.com
        http_etag: "..."
        list_id: bee.example.com
        member_id: 11
        role: member
        self_link: http://localhost:9001/3.0/members/11
        user: http://localhost:9001/3.0/users/7
    http_etag: "..."
    start: 0
    total_size: 1


Moderating a member
===================

The moderation action for a member can be changed by PATCH'ing the
`moderation_action` attribute.  When the member action falls back to the list
default, there is no such attribute in the resource.

    >>> dump_json('http://localhost:9001/3.0/members/10')
    address: http://localhost:9001/3.0/addresses/hperson@example.com
    delivery_mode: regular
    email: hperson@example.com
    http_etag: "..."
    list_id: ant.example.com
    member_id: 10
    role: member
    self_link: http://localhost:9001/3.0/members/10
    user: http://localhost:9001/3.0/users/7

Patching the moderation action both changes it for the given user, and adds
the attribute to the member's resource.
::

    >>> dump_json('http://localhost:9001/3.0/members/10', {
    ...           'moderation_action': 'hold',
    ...           }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/members/10')
    address: http://localhost:9001/3.0/addresses/hperson@example.com
    ...
    moderation_action: hold
    ...

It can be reset to the list default by patching an empty value.
::

    >>> dump_json('http://localhost:9001/3.0/members/10', {
    ...           'moderation_action': '',
    ...           }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/members/10')
    address: http://localhost:9001/3.0/addresses/hperson@example.com
    delivery_mode: regular
    email: hperson@example.com
    http_etag: "..."
    list_id: ant.example.com
    member_id: 10
    role: member
    self_link: http://localhost:9001/3.0/members/10
    user: http://localhost:9001/3.0/users/7


Handling the list of banned addresses
=====================================

To ban an address from subscribing you can POST to the ``/bans`` child
of any list using the REST API.

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com/bans',
    ...           {'email': 'banned@example.com'})
    content-length: 0
    ...
    location: .../3.0/lists/ant.example.com/bans/banned@example.com
    ...
    status: 201

This address is now banned, and you can get the list of banned addresses by
issuing a GET request on the ``/bans`` child.

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com/bans')
    entry 0:
        email: banned@example.com
        http_etag: "..."
        list_id: ant.example.com
        self_link: .../3.0/lists/ant.example.com/bans/banned@example.com
    ...

You can always GET a single banned address.

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/bans/banned@example.com')
    email: banned@example.com
    http_etag: "..."
    list_id: ant.example.com
    self_link: .../3.0/lists/ant.example.com/bans/banned@example.com

Unbanning addresses is also possible by issuing a DELETE request.

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/bans/banned@example.com',
    ...           method='DELETE')
    content-length: 0
    ...
    status: 204

After unbanning, the address is not shown in the ban list anymore.

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com/bans')
    http_etag: "..."
    start: 0
    total_size: 0

Global bans prevent an address from subscribing to any mailing list, and they
can be added via the top-level ``bans`` resource.

    >>> dump_json('http://localhost:9001/3.0/bans',
    ...           {'email': 'banned@example.com'})
    content-length: 0
    ...
    location: http://localhost:9001/3.0/bans/banned@example.com
    ...
    status: 201

Note that entries in the global bans do not have a ``list_id`` field.
::

    >>> dump_json('http://localhost:9001/3.0/bans')
    entry 0:
        email: banned@example.com
        http_etag: "..."
        self_link: http://localhost:9001/3.0/bans/banned@example.com
    ...

    >>> dump_json('http://localhost:9001/3.0/bans/banned@example.com')
    email: banned@example.com
    http_etag: "..."
    self_link: http://localhost:9001/3.0/bans/banned@example.com

As with list-centric bans, you can delete a global ban.

    >>> dump_json('http://localhost:9001/3.0/bans/banned@example.com',
    ...           method='DELETE')
    content-length: 0
    ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/bans/banned@example.com')
    Traceback (most recent call last):
    ...
    urllib.error.HTTPError: HTTP Error 404: ...
    >>> dump_json('http://localhost:9001/3.0/bans')
    http_etag: "..."
    start: 0
    total_size: 0


Mass Unsubscriptions
====================

A batch of users can be unsubscribed from the mailing list via the REST API
just by supplying their email addresses.
::

    >>> cat = create_list('cat@example.com')
    >>> subscribe(cat, 'Isla')
    <Member: Isla Person <iperson@example.com> on
             cat@example.com as MemberRole.member>
    >>> subscribe(cat, 'John')
    <Member: John Person <jperson@example.com> on
             cat@example.com as MemberRole.member>
    >>> subscribe(cat, 'Kate')
    <Member: Kate Person <kperson@example.com> on
             cat@example.com as MemberRole.member>

There are three new members of the mailing list.  We try to mass delete them,
plus one other address that isn't a member of the list.  We get back a
dictionary mapping email addresses to the success or failure of the removal
operation.  It's okay that one of the addresses is removed twice.

    >>> dump_json(
    ...     'http://localhost:9001/3.0/lists/cat.example.com/roster/member', {
    ...     'emails': ['iperson@example.com',
    ...                'jperson@example.com',
    ...                'iperson@example.com',
    ...                'zperson@example.com',
    ...                ]},
    ...     'DELETE')
    http_etag: "..."
    iperson@example.com: True
    jperson@example.com: True
    zperson@example.com: False

And now only Kate is still a member.

    >>> dump_json(
    ...     'http://localhost:9001/3.0/lists/cat.example.com/roster/member')
    entry 0:
        address: http://localhost:9001/3.0/addresses/kperson@example.com
        delivery_mode: regular
        email: kperson@example.com
        http_etag: "..."
        list_id: cat.example.com
        member_id: 14
        role: member
        self_link: http://localhost:9001/3.0/members/14
        user: http://localhost:9001/3.0/users/10
    ...
    total_size: 1
