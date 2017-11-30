====================
The pending database
====================

The pending database is where various types of events which need confirmation
are stored.  These can include email address registration events, held
messages (but only for user confirmation), auto-approvals, and probe bounces.
This is not where messages held for administrator approval are kept.

In order to pend an event, you first need a pending database.

    >>> from mailman.interfaces.pending import IPendings
    >>> from zope.component import getUtility
    >>> pendingdb = getUtility(IPendings)

There are nothing in the pendings database.

    >>> pendingdb.count
    0

The pending database can add any ``IPendable`` to the database, returning a
token that can be used in urls and such.
::

    >>> from zope.interface import implementer
    >>> from mailman.interfaces.pending import IPendable
    >>> @implementer(IPendable)
    ... class SimplePendable(dict):
    ...     PEND_TYPE = 'subscription'

    >>> subscription = SimplePendable(
    ...     address='aperson@example.com',
    ...     display_name='Anne Person',
    ...     language='en',
    ...     password='xyz')
    >>> token = pendingdb.add(subscription)
    >>> len(token)
    40

There's exactly one entry in the pendings database now.

    >>> pendingdb.count
    1

You can *confirm* the pending, which means returning the `IPendable` structure
(as a dictionary) from the database that matches the token.

All `IPendable` classes have a `PEND_TYPE` attribute which must be a string.
It is used to identify and query pendables in the database, and will be
returned as the `type` key in the dictionary.  Thus `type` is a reserved key
and pendables may not otherwise set it.

If the token isn't in the database, None is returned.

    >>> pendable = pendingdb.confirm(b'missing')
    >>> print(pendable)
    None
    >>> pendable = pendingdb.confirm(token)
    >>> dump_msgdata(pendable)
    address     : aperson@example.com
    display_name: Anne Person
    language    : en
    password    : xyz
    type        : subscription

After confirmation, the token is no longer in the database.

    >>> print(pendingdb.confirm(token))
    None

There are a few other things you can do with the pending database.  When you
confirm a token, you can leave it in the database, or in other words, not
expunge it.

    >>> event_1 = SimplePendable(type='one')
    >>> token_1 = pendingdb.add(event_1)
    >>> event_2 = SimplePendable(type='two')
    >>> token_2 = pendingdb.add(event_2)
    >>> event_3 = SimplePendable(type='three')
    >>> token_3 = pendingdb.add(event_3)
    >>> pendable = pendingdb.confirm(token_1, expunge=False)
    >>> dump_msgdata(pendable)
    type: one
    >>> pendable = pendingdb.confirm(token_1, expunge=True)
    >>> dump_msgdata(pendable)
    type: one
    >>> print(pendingdb.confirm(token_1))
    None

You can iterate over all the pendings in the database.

    >>> pendables = list(pendingdb)
    >>> def sort_key(item):
    ...     token, pendable = item
    ...     return pendable['type']
    >>> sorted_pendables = sorted(pendables, key=sort_key)
    >>> for token, pendable in sorted_pendables:
    ...     print(pendable['type'])
    three
    two

An event can be given a lifetime when it is pended, otherwise it just uses a
default lifetime.

    >>> from datetime import timedelta
    >>> yesterday = timedelta(days=-1)
    >>> event_4 = SimplePendable(type='four')
    >>> token_4 = pendingdb.add(event_4, lifetime=yesterday)

Every once in a while the pending database is cleared of old records.

    >>> pendingdb.evict()
    >>> print(pendingdb.confirm(token_4))
    None
    >>> pendable = pendingdb.confirm(token_2)
    >>> dump_msgdata(pendable)
    type: two
