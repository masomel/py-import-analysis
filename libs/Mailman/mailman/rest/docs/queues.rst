======
Queues
======

You can get information about what messages are currently in the Mailman
queues by querying the top-level ``queues`` resource.  Of course, this
information may be out-of-date by the time you receive a response, since queue
management is asynchronous, but the information will be as current as
possible.

You can get the list of all queue names.

    >>> dump_json('http://localhost:9001/3.0/queues')
    entry 0:
        count: 0
        directory: .../queue/archive
        files: []
        http_etag: ...
        name: archive
        self_link: http://localhost:9001/3.0/queues/archive
    entry 1:
        count: 0
        directory: .../queue/bad
        files: []
        http_etag: ...
        name: bad
        self_link: http://localhost:9001/3.0/queues/bad
    entry 2:
        count: 0
        directory: .../queue/bounces
        files: []
        http_etag: ...
        name: bounces
        self_link: http://localhost:9001/3.0/queues/bounces
    entry 3:
        count: 0
        directory: .../queue/command
        files: []
        http_etag: ...
        name: command
        self_link: http://localhost:9001/3.0/queues/command
    entry 4:
        count: 0
        directory: .../queue/digest
        files: []
        http_etag: ...
        name: digest
        self_link: http://localhost:9001/3.0/queues/digest
    entry 5:
        count: 0
        directory: .../queue/in
        files: []
        http_etag: ...
        name: in
        self_link: http://localhost:9001/3.0/queues/in
    entry 6:
        count: 0
        directory: .../queue/nntp
        files: []
        http_etag: ...
        name: nntp
        self_link: http://localhost:9001/3.0/queues/nntp
    entry 7:
        count: 0
        directory: .../queue/out
        files: []
        http_etag: ...
        name: out
        self_link: http://localhost:9001/3.0/queues/out
    entry 8:
        count: 0
        directory: .../queue/pipeline
        files: []
        http_etag: ...
        name: pipeline
        self_link: http://localhost:9001/3.0/queues/pipeline
    entry 9:
        count: 0
        directory: .../queue/retry
        files: []
        http_etag: ...
        name: retry
        self_link: http://localhost:9001/3.0/queues/retry
    entry 10:
        count: 0
        directory: .../queue/shunt
        files: []
        http_etag: ...
        name: shunt
        self_link: http://localhost:9001/3.0/queues/shunt
    entry 11:
        count: 0
        directory: .../queue/virgin
        files: []
        http_etag: ...
        name: virgin
        self_link: http://localhost:9001/3.0/queues/virgin
    http_etag: ...
    self_link: http://localhost:9001/3.0/queues
    start: 0
    total_size: 12

Query an individual queue to get a count of, and the list of file base names
in the queue.  There are currently no files in the ``bad`` queue.

    >>> dump_json('http://localhost:9001/3.0/queues/bad')
    count: 0
    directory: .../queue/bad
    files: []
    http_etag: ...
    name: bad
    self_link: http://localhost:9001/3.0/queues/bad

We can inject a message into the ``bad`` queue.  It must be destined for an
existing mailing list.

    >>> dump_json('http://localhost:9001/3.0/lists', {
    ...     'fqdn_listname': 'ant@example.com',
    ...     })
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/lists/ant.example.com
    server: WSGIServer/0.2 CPython/...
    status: 201

While list creation takes an FQDN list name, injecting a message to the queue
requires a List ID.

    >>> dump_json('http://localhost:9001/3.0/queues/bad', {
    ...     'list_id': 'ant.example.com',
    ...     'text': """\
    ... From: anne@example.com
    ... To: ant@example.com
    ... Subject: Testing
    ...
    ... """})
    content-length: 0
    content-type: application/json; charset=UTF-8
    date: ...
    location: http://localhost:9001/3.0/queues/bad/...
    server: ...
    status: 201

And now the ``bad`` queue has at least one message in it.

    >>> dump_json('http://localhost:9001/3.0/queues/bad')
    count: 1
    directory: .../queue/bad
    files: ['...']
    http_etag: ...
    name: bad
    self_link: http://localhost:9001/3.0/queues/bad

We can delete the injected message.

    >>> json = call_http('http://localhost:9001/3.0/queues/bad')
    >>> len(json['files'])
    1
    >>> dump_json('http://localhost:9001/3.0/queues/bad/{}'.format(
    ...           json['files'][0]),
    ...           method='DELETE')
    content-length: 0
    date: ...
    server: ...
    status: 204

And now the queue has no files.

    >>> dump_json('http://localhost:9001/3.0/queues/bad')
    count: 0
    directory: .../queue/bad
    files: []
    http_etag: ...
    name: bad
    self_link: http://localhost:9001/3.0/queues/bad
