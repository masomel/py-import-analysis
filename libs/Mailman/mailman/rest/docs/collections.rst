============================
 Collections and Pagination
============================

All collections automatically support pagination.  You can use this to limit
the number of items of the collection that get returned, and you can page
through the results by incrementing the page counter.

For example, let's say we have 50 mailing lists.

    >>> from mailman.app.lifecycle import create_list
    >>> for i in range(50):
    ...     mlist = create_list('list{:02d}@example.com'.format(i))
    >>> transaction.commit()

We can get the first 10 lists by asking for the first page of items.

    >>> json = call_http('http://localhost:9001/3.0/lists?count=10&page=1')
    >>> for entry in json['entries']:
    ...     print(entry['list_id'])
    list00.example.com
    list01.example.com
    list02.example.com
    list03.example.com
    list04.example.com
    list05.example.com
    list06.example.com
    list07.example.com
    list08.example.com
    list09.example.com

We can also ask for the third set of 10 mailing lists.

    >>> json = call_http('http://localhost:9001/3.0/lists?count=10&page=3')
    >>> for entry in json['entries']:
    ...     print(entry['list_id'])
    list20.example.com
    list21.example.com
    list22.example.com
    list23.example.com
    list24.example.com
    list25.example.com
    list26.example.com
    list27.example.com
    list28.example.com
    list29.example.com

Of course, we can also adjust the page size and ask for the tenth page of 5
mailing lists.

    >>> json = call_http('http://localhost:9001/3.0/lists?count=5&page=10')
    >>> for entry in json['entries']:
    ...     print(entry['list_id'])
    list45.example.com
    list46.example.com
    list47.example.com
    list48.example.com
    list49.example.com


The size of a collection
========================

This same idiom allows you to get just the size of the collection.  You do
this by asking for a page of size zero.

    >>> dump_json('http://localhost:9001/3.0/lists?count=0&page=1')
    http_etag: ...
    start: 0
    total_size: 50


Page start
==========

Notice the `start` element in the returned JSON.  This tells you which item of
the collection the page starts on.

    >>> dump_json('http://localhost:9001/3.0/lists?count=2&page=15')
    entry 0:
        display_name: List28
        ...
    entry 1:
        display_name: List29
        ...
    http_etag: ...
    start: 28
    total_size: 50
