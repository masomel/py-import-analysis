.. _model-requests:

==================
Moderator requests
==================

Various actions will be held for moderator approval, such as subscriptions to
closed lists, or postings by non-members.  The requests database is the low
level interface to these actions requiring approval.

An :ref:`application level interface <app-moderator>` for holding messages and
membership changes is also available.


Mailing list-centric
====================

A set of requests are always related to a particular mailing list.  Adapt the
mailing list to get its requests.
::

    >>> from mailman.interfaces.requests import IListRequests
    >>> from zope.interface.verify import verifyObject

    >>> mlist = create_list('test@example.com')
    >>> requests = IListRequests(mlist)
    >>> verifyObject(IListRequests, requests)
    True
    >>> requests.mailing_list
    <mailing list "test@example.com" at ...>


Holding requests
================

The list's requests database starts out empty.

    >>> print(requests.count)
    0
    >>> dump_list(requests.held_requests)
    *Empty*

At the lowest level, the requests database is very simple.  Holding a request
requires a request type (as an enum value), a key, and an optional dictionary
of associated data.  The request database assigns no semantics to the held
data, except for the request type.

    >>> from mailman.interfaces.requests import RequestType

We can hold messages for moderator approval.

    >>> requests.hold_request(RequestType.held_message, 'hold_1')
    1

We can hold subscription requests for moderator approval.

    >>> requests.hold_request(RequestType.subscription, 'hold_2')
    2

We can hold unsubscription requests for moderator approval.

    >>> requests.hold_request(RequestType.unsubscription, 'hold_3')
    3


Getting requests
================

We can see the total number of requests being held.

    >>> print(requests.count)
    3

We can also see the number of requests being held by request type.

    >>> print(requests.count_of(RequestType.subscription))
    1
    >>> print(requests.count_of(RequestType.unsubscription))
    1

We can also see when there are multiple held requests of a particular type.

    >>> print(requests.hold_request(RequestType.held_message, 'hold_4'))
    4
    >>> print(requests.count_of(RequestType.held_message))
    2

We can ask the requests database for a specific request, by providing the id
of the request data we want.  This returns a 2-tuple of the key and data we
originally held.

    >>> key, data = requests.get_request(2)
    >>> print(key)
    hold_2

There was no additional data associated with request 2.

    >>> print(data)
    None

If we ask for a request that is not in the database, we get None back.

    >>> print(requests.get_request(801))
    None


Additional data
===============

When a request is held, additional data can be associated with it, in the form
of a dictionary with string values.

    >>> data = dict(foo='yes', bar='no')
    >>> requests.hold_request(RequestType.held_message, 'hold_5', data)
    5

The data is returned when the request is retrieved.  The dictionary will have
an additional key which holds the name of the request type.

    >>> key, data = requests.get_request(5)
    >>> print(key)
    hold_5
    >>> dump_msgdata(data)
    _request_type: held_message
    bar          : no
    foo          : yes
    type         : data


Iterating over requests
=======================

To make it easier to find specific requests, the list requests can be iterated
over by type.

    >>> print(requests.count_of(RequestType.held_message))
    3
    >>> for request in requests.of_type(RequestType.held_message):
    ...     key, data = requests.get_request(request.id)
    ...     print(request.id, request.request_type, key)
    ...     if data is not None:
    ...         for key in sorted(data):
    ...             print('    {0}: {1}'.format(key, data[key]))
    1 RequestType.held_message hold_1
    4 RequestType.held_message hold_4
    5 RequestType.held_message hold_5
        _request_type: held_message
        bar: no
        foo: yes
        type: data


Deleting requests
=================

Once a specific request has been handled, it can be deleted from the requests
database.

    >>> print(requests.count)
    5
    >>> requests.delete_request(2)
    >>> print(requests.count)
    4

Request 2 is no longer in the database.

    >>> print(requests.get_request(2))
    None

    >>> for request in requests.held_requests:
    ...     requests.delete_request(request.id)
    >>> print(requests.count)
    0
