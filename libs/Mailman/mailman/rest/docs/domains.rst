=======
Domains
=======

`Domains`_ are how Mailman interacts with email host names and web host names.
::

    # The test framework starts out with an example domain, so let's delete
    # that first.
    >>> from mailman.interfaces.domain import IDomainManager
    >>> from zope.component import getUtility
    >>> domain_manager = getUtility(IDomainManager)

    >>> domain_manager.remove('example.com')
    <Domain example.com...>
    >>> transaction.commit()

The REST API can be queried for the set of known domains, of which there are
initially none.

    >>> dump_json('http://localhost:9001/3.0/domains')
    http_etag: "..."
    start: 0
    total_size: 0

Once a domain is added, it is accessible through the API.
::

    >>> domain_manager.add('example.com', 'An example domain')
    <Domain example.com, An example domain>
    >>> transaction.commit()

    >>> dump_json('http://localhost:9001/3.0/domains')
    entry 0:
        description: An example domain
        http_etag: "..."
        mail_host: example.com
        self_link: http://localhost:9001/3.0/domains/example.com
    http_etag: "..."
    start: 0
    total_size: 1

At the top level, all domains are returned as separate entries.
::

    >>> domain_manager.add('example.org',)
    <Domain example.org>
    >>> domain_manager.add(
    ...     'lists.example.net',
    ...     'Porkmasters')
    <Domain lists.example.net, Porkmasters>
    >>> transaction.commit()

    >>> dump_json('http://localhost:9001/3.0/domains')
    entry 0:
        description: An example domain
        http_etag: "..."
        mail_host: example.com
        self_link: http://localhost:9001/3.0/domains/example.com
    entry 1:
        description: None
        http_etag: "..."
        mail_host: example.org
        self_link: http://localhost:9001/3.0/domains/example.org
    entry 2:
        description: Porkmasters
        http_etag: "..."
        mail_host: lists.example.net
        self_link: http://localhost:9001/3.0/domains/lists.example.net
    http_etag: "..."
    start: 0
    total_size: 3


Individual domains
==================

The information for a single domain is available by following one of the
``self_links`` from the above collection.

    >>> dump_json('http://localhost:9001/3.0/domains/lists.example.net')
    description: Porkmasters
    http_etag: "..."
    mail_host: lists.example.net
    self_link: http://localhost:9001/3.0/domains/lists.example.net

You can also list all the mailing lists for a given domain.  At first, the
example.com domain does not contain any mailing lists.
::

    >>> dump_json('http://localhost:9001/3.0/domains/example.com/lists')
    http_etag: "..."
    start: 0
    total_size: 0

    >>> dump_json('http://localhost:9001/3.0/lists', {
    ...           'fqdn_listname': 'test-domains@example.com',
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/lists/test-domains.example.com
    ...

    >>> dump_json('http://localhost:9001/3.0/domains/example.com/lists')
    entry 0:
        display_name: Test-domains
        fqdn_listname: test-domains@example.com
        http_etag: "..."
        ...
        member_count: 0
        self_link: http://localhost:9001/3.0/lists/test-domains.example.com
        volume: 1
    http_etag: "..."
    start: 0
    total_size: 1

Other domains continue to contain no mailing lists.

    >>> dump_json('http://localhost:9001/3.0/domains/lists.example.net/lists')
    http_etag: "..."
    start: 0
    total_size: 0


Creating new domains
====================

New domains can be created by posting to the ``domains`` url.

    >>> dump_json('http://localhost:9001/3.0/domains', {
    ...           'mail_host': 'lists.example.com',
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/domains/lists.example.com
    ...

Now the web service knows about our new domain.

    >>> dump_json('http://localhost:9001/3.0/domains/lists.example.com')
    description: None
    http_etag: "..."
    mail_host: lists.example.com
    self_link: http://localhost:9001/3.0/domains/lists.example.com

And the new domain is in our database.
::

    >>> domain_manager['lists.example.com']
    <Domain lists.example.com>

    # Unlock the database.
    >>> transaction.abort()

You can also create a new domain with a description and a contact address.
::

    >>> dump_json('http://localhost:9001/3.0/domains', {
    ...           'mail_host': 'my.example.com',
    ...           'description': 'My new domain',
    ...           })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/domains/my.example.com
    ...

    >>> dump_json('http://localhost:9001/3.0/domains/my.example.com')
    description: My new domain
    http_etag: "..."
    mail_host: my.example.com
    self_link: http://localhost:9001/3.0/domains/my.example.com

    >>> domain_manager['my.example.com']
    <Domain my.example.com, My new domain>

    # Unlock the database.
    >>> transaction.abort()


Deleting domains
================

Domains can also be deleted via the API.

    >>> dump_json('http://localhost:9001/3.0/domains/lists.example.com',
    ...           method='DELETE')
    content-length: 0
    date: ...
    server: ...
    status: 204


Domain owners
=============

Domains can have owners.  By posting some addresses to the owners resource,
you can add some domain owners.  Currently our domain has no owners:

    >>> dump_json('http://localhost:9001/3.0/domains/my.example.com/owners')
    http_etag: ...
    start: 0
    total_size: 0

Anne and Bart volunteer to be a domain owners.
::

    >>> dump_json('http://localhost:9001/3.0/domains/my.example.com/owners', (
    ...     ('owner', 'anne@example.com'), ('owner', 'bart@example.com')
    ...     ))
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/domains/my.example.com/owners')
    entry 0:
        created_on: 2005-08-01T07:49:23
        http_etag: ...
        is_server_owner: False
        self_link: http://localhost:9001/3.0/users/1
        user_id: 1
    entry 1:
        created_on: 2005-08-01T07:49:23
        http_etag: ...
        is_server_owner: False
        self_link: http://localhost:9001/3.0/users/2
        user_id: 2
    http_etag: ...
    start: 0
    total_size: 2

We can delete all the domain owners.

    >>> dump_json('http://localhost:9001/3.0/domains/my.example.com/owners',
    ...           method='DELETE')
    content-length: 0
    date: ...
    server: ...
    status: 204

Now there are no owners.

    >>> dump_json('http://localhost:9001/3.0/domains/my.example.com/owners')
    http_etag: ...
    start: 0
    total_size: 0

New domains can be created with owners.

    >>> dump_json('http://localhost:9001/3.0/domains', (
    ...           ('mail_host', 'your.example.com'),
    ...           ('owner', 'anne@example.com'),
    ...           ('owner', 'bart@example.com'),
    ...           ))
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/domains/your.example.com
    server: ...
    status: 201

The new domain has the expected owners.

    >>> dump_json('http://localhost:9001/3.0/domains/your.example.com/owners')
    entry 0:
        created_on: 2005-08-01T07:49:23
        http_etag: ...
        is_server_owner: False
        self_link: http://localhost:9001/3.0/users/1
        user_id: 1
    entry 1:
        created_on: 2005-08-01T07:49:23
        http_etag: ...
        is_server_owner: False
        self_link: http://localhost:9001/3.0/users/2
        user_id: 2
    http_etag: ...
    start: 0
    total_size: 2


.. _Domains: ../../model/docs/domains.html
