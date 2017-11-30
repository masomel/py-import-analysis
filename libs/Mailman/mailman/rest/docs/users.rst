=====
Users
=====

The REST API can be used to add and remove users, add and remove user
addresses, and change their preferred address, password, or name.  The API can
also be used to verify a user's password.

Users are different than members; the latter represents an email address
subscribed to a specific mailing list.  Users are just people that Mailman
knows about.

There are no users yet.

    >>> dump_json('http://localhost:9001/3.0/users')
    http_etag: "..."
    start: 0
    total_size: 0

Anne is added, with an email address.  Her user record gets a `user_id`.

    >>> from zope.component import getUtility
    >>> from mailman.interfaces.usermanager import IUserManager
    >>> user_manager = getUtility(IUserManager)
    >>> anne = user_manager.create_user('anne@example.com', 'Anne Person')
    >>> transaction.commit()
    >>> int(anne.user_id.int)
    1

Anne's user record is returned as an entry into the collection of all users.

    >>> dump_json('http://localhost:9001/3.0/users')
    entry 0:
        created_on: 2005-08-01T07:49:23
        display_name: Anne Person
        http_etag: "..."
        is_server_owner: False
        self_link: http://localhost:9001/3.0/users/1
        user_id: 1
    http_etag: "..."
    start: 0
    total_size: 1

A user might not have a display name, in which case, the attribute will not be
returned in the REST API.

    >>> bart = user_manager.create_user('bart@example.com')
    >>> transaction.commit()
    >>> dump_json('http://localhost:9001/3.0/users')
    entry 0:
        created_on: 2005-08-01T07:49:23
        display_name: Anne Person
        http_etag: "..."
        is_server_owner: False
        self_link: http://localhost:9001/3.0/users/1
        user_id: 1
    entry 1:
        created_on: 2005-08-01T07:49:23
        http_etag: "..."
        is_server_owner: False
        self_link: http://localhost:9001/3.0/users/2
        user_id: 2
    http_etag: "..."
    start: 0
    total_size: 2


Paginating over user records
----------------------------

Instead of returning all the user records at once, it's possible to return
them in pages by adding the GET parameters ``count`` and ``page`` to the
request URI.  Page 1 is the first page and ``count`` defines the size of the
page.
::

    >>> dump_json('http://localhost:9001/3.0/users?count=1&page=1')
    entry 0:
        created_on: 2005-08-01T07:49:23
        display_name: Anne Person
        http_etag: "..."
        is_server_owner: False
        self_link: http://localhost:9001/3.0/users/1
        user_id: 1
    http_etag: "..."
    start: 0
    total_size: 2

    >>> dump_json('http://localhost:9001/3.0/users?count=1&page=2')
    entry 0:
        created_on: 2005-08-01T07:49:23
        http_etag: "..."
        is_server_owner: False
        self_link: http://localhost:9001/3.0/users/2
        user_id: 2
    http_etag: "..."
    start: 1
    total_size: 2


Creating users
==============

New users can be created by POSTing to the users collection.  At a minimum,
the user's email address must be provided.

    >>> dump_json('http://localhost:9001/3.0/users', {
    ...           'email': 'cris@example.com',
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/users/3
    server: ...
    status: 201

Cris is now a user known to the system, but he has no display name.

    >>> user_manager.get_user('cris@example.com')
    <User "" (3) at ...>

Cris's user record can also be accessed via the REST API, using her user id.
Note that because no password was given when the record was created, a random
one was assigned to her.

    >>> dump_json('http://localhost:9001/3.0/users/3')
    created_on: 2005-08-01T07:49:23
    http_etag: "..."
    is_server_owner: False
    password: {plaintext}...
    self_link: http://localhost:9001/3.0/users/3
    user_id: 3

Because email addresses just have an ``@`` sign in then, there's no confusing
them with user ids.  Thus, Cris's record can be retrieved via her email
address.

    >>> dump_json('http://localhost:9001/3.0/users/cris@example.com')
    created_on: 2005-08-01T07:49:23
    http_etag: "..."
    is_server_owner: False
    password: {plaintext}...
    self_link: http://localhost:9001/3.0/users/3
    user_id: 3


Providing a display name
------------------------

When a user is added, a display name can be provided.

    >>> transaction.abort()
    >>> dump_json('http://localhost:9001/3.0/users', {
    ...           'email': 'dave@example.com',
    ...           'display_name': 'Dave Person',
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/users/4
    server: ...
    status: 201

Dave's user record includes his display name.

    >>> dump_json('http://localhost:9001/3.0/users/4')
    created_on: 2005-08-01T07:49:23
    display_name: Dave Person
    http_etag: "..."
    is_server_owner: False
    password: {plaintext}...
    self_link: http://localhost:9001/3.0/users/4
    user_id: 4


Providing passwords
-------------------

To avoid getting assigned a random, and irretrievable password (but one which
can be reset), you can provide a password when the user is created.  By
default, the password is provided in plain text, and it is hashed by Mailman
before being stored.

    >>> transaction.abort()
    >>> dump_json('http://localhost:9001/3.0/users', {
    ...           'email': 'elly@example.com',
    ...           'display_name': 'Elly Person',
    ...           'password': 'supersekrit',
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/users/5
    server: ...
    status: 201

When we view Elly's user record, we can tell that her password has been hashed
because it has the hash algorithm prefix (i.e. the *{plaintext}* marker).

    >>> dump_json('http://localhost:9001/3.0/users/5')
    created_on: 2005-08-01T07:49:23
    display_name: Elly Person
    http_etag: "..."
    is_server_owner: False
    password: {plaintext}supersekrit
    self_link: http://localhost:9001/3.0/users/5
    user_id: 5


Updating users
==============

Dave's display name can be changed through the REST API.

    >>> dump_json('http://localhost:9001/3.0/users/4', {
    ...           'display_name': 'David Person',
    ...           }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

Dave's display name has been updated.

    >>> dump_json('http://localhost:9001/3.0/users/dave@example.com')
    created_on: 2005-08-01T07:49:23
    display_name: David Person
    http_etag: "..."
    is_server_owner: False
    password: {plaintext}...
    self_link: http://localhost:9001/3.0/users/4
    user_id: 4

Dave can also be assigned a new password by providing in the new cleartext
password.  Mailman will hash this before it is stored internally.

    >>> dump_json('http://localhost:9001/3.0/users/4', {
    ...           'cleartext_password': 'clockwork angels',
    ...           }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

As described above, even though you see *{plaintext}clockwork angels* below,
it has still been hashed before storage.  The default hashing algorithm for
the test suite is a plain text hash, but you can see that it works by the
addition of the algorithm prefix.

    >>> dump_json('http://localhost:9001/3.0/users/4')
    created_on: 2005-08-01T07:49:23
    display_name: David Person
    http_etag: "..."
    is_server_owner: False
    password: {plaintext}clockwork angels
    self_link: http://localhost:9001/3.0/users/4
    user_id: 4

You can change both the display name and the password by PUTing the full
resource.

    >>> dump_json('http://localhost:9001/3.0/users/4', {
    ...           'cleartext_password': 'the garden',
    ...           'display_name': 'David Personhood',
    ...           'is_server_owner': False,
    ...           }, method='PUT')
    content-length: 0
    date: ...
    server: ...
    status: 204

Dave's user record has been updated.

    >>> dump_json('http://localhost:9001/3.0/users/dave@example.com')
    created_on: 2005-08-01T07:49:23
    display_name: David Personhood
    http_etag: "..."
    is_server_owner: False
    password: {plaintext}the garden
    self_link: http://localhost:9001/3.0/users/4
    user_id: 4


Deleting users via the API
==========================

Users can also be deleted via the API.

    >>> dump_json('http://localhost:9001/3.0/users/cris@example.com',
    ...           method='DELETE')
    content-length: 0
    date: ...
    server: ...
    status: 204


User addresses
==============

Fred may have any number of email addresses associated with his user account,
and we can find them all through the API.

Through some other means, Fred registers a bunch of email addresses and
associates them with his user account.

    >>> fred = user_manager.create_user('fred@example.com', 'Fred Person')
    >>> fred.register('fperson@example.com')
    <Address: fperson@example.com [not verified] at ...>
    >>> fred.register('fred.person@example.com')
    <Address: fred.person@example.com [not verified] at ...>
    >>> fred.register('Fred.Q.Person@example.com')
    <Address: Fred.Q.Person@example.com [not verified]
              key: fred.q.person@example.com at ...>
    >>> transaction.commit()

When we access Fred's addresses via the REST API, they are sorted in lexical
order by original (i.e. case-preserved) email address.

    >>> dump_json('http://localhost:9001/3.0/users/fred@example.com/addresses')
    entry 0:
        email: fred.q.person@example.com
        http_etag: "..."
        original_email: Fred.Q.Person@example.com
        registered_on: 2005-08-01T07:49:23
        self_link:
            http://localhost:9001/3.0/addresses/fred.q.person@example.com
        user: http://localhost:9001/3.0/users/6
    entry 1:
        email: fperson@example.com
        http_etag: "..."
        original_email: fperson@example.com
        registered_on: 2005-08-01T07:49:23
        self_link: http://localhost:9001/3.0/addresses/fperson@example.com
        user: http://localhost:9001/3.0/users/6
    entry 2:
        email: fred.person@example.com
        http_etag: "..."
        original_email: fred.person@example.com
        registered_on: 2005-08-01T07:49:23
        self_link: http://localhost:9001/3.0/addresses/fred.person@example.com
        user: http://localhost:9001/3.0/users/6
    entry 3:
        display_name: Fred Person
        email: fred@example.com
        http_etag: "..."
        original_email: fred@example.com
        registered_on: 2005-08-01T07:49:23
        self_link: http://localhost:9001/3.0/addresses/fred@example.com
        user: http://localhost:9001/3.0/users/6
    http_etag: "..."
    start: 0
    total_size: 4

In fact, since these are all associated with Fred's user account, any of the
addresses can be used to look up Fred's user record.
::

    >>> dump_json('http://localhost:9001/3.0/users/fred@example.com')
    created_on: 2005-08-01T07:49:23
    display_name: Fred Person
    http_etag: "..."
    is_server_owner: False
    self_link: http://localhost:9001/3.0/users/6
    user_id: 6

    >>> dump_json('http://localhost:9001/3.0/users/fred.person@example.com')
    created_on: 2005-08-01T07:49:23
    display_name: Fred Person
    http_etag: "..."
    is_server_owner: False
    self_link: http://localhost:9001/3.0/users/6
    user_id: 6

    >>> dump_json('http://localhost:9001/3.0/users/fperson@example.com')
    created_on: 2005-08-01T07:49:23
    display_name: Fred Person
    http_etag: "..."
    is_server_owner: False
    self_link: http://localhost:9001/3.0/users/6
    user_id: 6

    >>> dump_json('http://localhost:9001/3.0/users/Fred.Q.Person@example.com')
    created_on: 2005-08-01T07:49:23
    display_name: Fred Person
    http_etag: "..."
    is_server_owner: False
    self_link: http://localhost:9001/3.0/users/6
    user_id: 6


Verifying passwords
===================

A user's password is stored internally in hashed form.  Logging in a user is
the process of verifying a provided clear text password against the hashed
internal password.

When Elly was added as a user, she provided a password in the clear.  Now the
password is hashed and getting her user record returns the hashed password.

    >>> dump_json('http://localhost:9001/3.0/users/5')
    created_on: 2005-08-01T07:49:23
    display_name: Elly Person
    http_etag: "..."
    is_server_owner: False
    password: {plaintext}supersekrit
    self_link: http://localhost:9001/3.0/users/5
    user_id: 5

Unless the client can run the hashing algorithm on the login text that Elly
provided, and do its own comparison, the client should let the REST API handle
password verification.

This time, Elly successfully logs into Mailman.

    >>> dump_json('http://localhost:9001/3.0/users/5/login', {
    ...           'cleartext_password': 'supersekrit',
    ...           }, method='POST')
    content-length: 0
    date: ...
    server: ...
    status: 204


Server owners
=============

Users can be designated as server owners.  Elly is not currently a server
owner.

    >>> dump_json('http://localhost:9001/3.0/users/5')
    created_on: 2005-08-01T07:49:23
    display_name: Elly Person
    http_etag: "..."
    is_server_owner: False
    password: {plaintext}supersekrit
    self_link: http://localhost:9001/3.0/users/5
    user_id: 5

Let's make her a server owner.
::

    >>> dump_json('http://localhost:9001/3.0/users/5', {
    ...           'is_server_owner': True,
    ...           }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/users/5')
    created_on: 2005-08-01T07:49:23
    display_name: Elly Person
    http_etag: "..."
    is_server_owner: True
    password: {plaintext}supersekrit
    self_link: http://localhost:9001/3.0/users/5
    user_id: 5

Elly later retires as server owner.
::

    >>> dump_json('http://localhost:9001/3.0/users/5', {
    ...           'is_server_owner': False,
    ...           }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/users/5')
    created_on: 2005-08-01T07:49:23
    display_name: Elly Person
    http_etag: "..."
    is_server_owner: False
    password: {plaintext}...
    self_link: http://localhost:9001/3.0/users/5
    user_id: 5

Gwen, a new users, takes over as a server owner.
::

    >>> dump_json('http://localhost:9001/3.0/users', {
    ...           'display_name': 'Gwen Person',
    ...           'email': 'gwen@example.com',
    ...           'is_server_owner': True,
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/users/7
    server: ...
    status: 201

    >>> dump_json('http://localhost:9001/3.0/users/7')
    created_on: 2005-08-01T07:49:23
    display_name: Gwen Person
    http_etag: "..."
    is_server_owner: True
    password: {plaintext}...
    self_link: http://localhost:9001/3.0/users/7
    user_id: 7


Linking users
=============

If an address already exists, but is not yet linked to a user, and a new user
is requested for that address, the user will be linked to the existing
address.

Herb's address already exists, but no user is linked to it.

    >>> herb = user_manager.create_address('herb@example.com')
    >>> print(herb.user)
    None
    >>> transaction.commit()

Now, a user creation request is received, using Herb's email address.

    >>> dump_json('http://localhost:9001/3.0/users', {
    ...           'email': 'herb@example.com',
    ...           'display_name': 'Herb Person',
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/users/8
    server: ...
    status: 201

Herb's email address is now linked to the new user.

    >>> herb.user
    <User "Herb Person" (8) at ...
