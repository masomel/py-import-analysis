===============
 Server owners
===============

Certain users can be designated as *server owners*.  This role has no direct
function in the core, but it can be used by clients of the REST API to
determine additional permissions.  For example, Postorius might allow server
owners to create new domains.

Initially, there are no server owners.

    >>> dump_json('http://localhost:9001/3.0/owners')
    http_etag: "..."
    start: 0
    total_size: 0

When new users are created in the core, they do not become server owners by
default.

    >>> from zope.component import getUtility
    >>> from mailman.interfaces.usermanager import IUserManager
    >>> user_manager = getUtility(IUserManager)
    >>> anne = user_manager.create_user('anne@example.com', 'Anne Person')
    >>> transaction.commit()
    >>> dump_json('http://localhost:9001/3.0/owners')
    http_etag: "..."
    start: 0
    total_size: 0

Anne's server owner flag is set.

    >>> anne.is_server_owner = True
    >>> transaction.commit()

And now we can find her user record.

    >>> dump_json('http://localhost:9001/3.0/owners')
    entry 0:
        created_on: 2005-08-01T07:49:23
        display_name: Anne Person
        http_etag: "..."
        is_server_owner: True
        self_link: http://localhost:9001/3.0/users/1
        user_id: 1
    http_etag: "..."
    start: 0
    total_size: 1

Bart and Cate are also users, but not server owners.

    >>> bart = user_manager.create_user('bart@example.com', 'Bart Person')
    >>> cate = user_manager.create_user('cate@example.com', 'Cate Person')
    >>> transaction.commit()
    >>> dump_json('http://localhost:9001/3.0/owners')
    entry 0:
        created_on: 2005-08-01T07:49:23
        display_name: Anne Person
        http_etag: "..."
        is_server_owner: True
        self_link: http://localhost:9001/3.0/users/1
        user_id: 1
    http_etag: "..."
    start: 0
    total_size: 1

Anne retires as a server owner, with Bart and Cate taking over.

    >>> anne.is_server_owner = False
    >>> bart.is_server_owner = True
    >>> cate.is_server_owner = True
    >>> transaction.commit()
    >>> dump_json('http://localhost:9001/3.0/owners')
    entry 0:
        created_on: 2005-08-01T07:49:23
        display_name: Bart Person
        http_etag: "..."
        is_server_owner: True
        self_link: http://localhost:9001/3.0/users/2
        user_id: 2
    entry 1:
        created_on: 2005-08-01T07:49:23
        display_name: Cate Person
        http_etag: "..."
        is_server_owner: True
        self_link: http://localhost:9001/3.0/users/3
        user_id: 3
    http_etag: "..."
    start: 0
    total_size: 2
