===============
Post Moderation
===============

Messages which are held for approval can be accepted, rejected, discarded, or
deferred by the list moderators.


Viewing the list of held messages
=================================

Held messages can be moderated through the REST API.  A mailing list starts
with no held messages.

    >>> ant = create_list('ant@example.com')
    >>> transaction.commit()
    >>> dump_json('http://localhost:9001/3.0/lists/ant@example.com/held')
    http_etag: "..."
    start: 0
    total_size: 0

When a message gets held for moderator approval, it shows up in this list.
::

    >>> msg = message_from_string("""\
    ... From: anne@example.com
    ... To: ant@example.com
    ... Subject: Something
    ... Message-ID: <alpha>
    ...
    ... Something else.
    ... """)

    >>> from mailman.app.moderator import hold_message
    >>> request_id = hold_message(ant, msg, {'extra': 7}, 'Because')
    >>> transaction.commit()

    >>> dump_json('http://localhost:9001/3.0/lists/ant@example.com/held')
    entry 0:
        extra: 7
        hold_date: 2005-08-01T07:49:23
        http_etag: "..."
        message_id: <alpha>
        msg: From: anne@example.com
    To: ant@example.com
    Subject: Something
    Message-ID: <alpha>
    Message-ID-Hash: XZ3DGG4V37BZTTLXNUX4NABB4DNQHTCP
    X-Message-ID-Hash: XZ3DGG4V37BZTTLXNUX4NABB4DNQHTCP
    <BLANKLINE>
    Something else.
    <BLANKLINE>
        original_subject: Something
        reason: Because
        request_id: 1
        self_link: http://localhost:9001/3.0/lists/ant.example.com/held/1
        sender: anne@example.com
        subject: Something
    http_etag: "..."
    start: 0
    total_size: 1

You can get an individual held message by providing the *request id* for that
message.  This will include the text of the message.
::

    >>> def url(request_id):
    ...     return ('http://localhost:9001/3.0/lists/'
    ...             'ant@example.com/held/{0}'.format(request_id))

    >>> dump_json(url(request_id))
    extra: 7
    hold_date: 2005-08-01T07:49:23
    http_etag: "..."
    message_id: <alpha>
    msg: From: anne@example.com
    To: ant@example.com
    Subject: Something
    Message-ID: <alpha>
    Message-ID-Hash: XZ3DGG4V37BZTTLXNUX4NABB4DNQHTCP
    X-Message-ID-Hash: XZ3DGG4V37BZTTLXNUX4NABB4DNQHTCP
    <BLANKLINE>
    Something else.
    <BLANKLINE>
    original_subject: Something
    reason: Because
    request_id: 1
    self_link: http://localhost:9001/3.0/lists/ant.example.com/held/1
    sender: anne@example.com
    subject: Something


Disposing of held messages
==========================

Individual messages can be moderated through the API by POSTing back to the
held message's resource.   The POST data requires an action of one of the
following:

  * discard - throw the message away.
  * reject - bounces the message back to the original author.
  * defer - defer any action on the message (continue to hold it)
  * accept - accept the message for posting.

Let's see what happens when the above message is deferred.

    >>> dump_json(url(request_id), {
    ...     'action': 'defer',
    ...     })
    content-length: 0
    date: ...
    server: ...
    status: 204

The message is still in the moderation queue.

    >>> dump_json(url(request_id))
    extra: 7
    hold_date: 2005-08-01T07:49:23
    http_etag: "..."
    message_id: <alpha>
    msg: From: anne@example.com
    To: ant@example.com
    Subject: Something
    Message-ID: <alpha>
    Message-ID-Hash: XZ3DGG4V37BZTTLXNUX4NABB4DNQHTCP
    X-Message-ID-Hash: XZ3DGG4V37BZTTLXNUX4NABB4DNQHTCP
    <BLANKLINE>
    Something else.
    <BLANKLINE>
    original_subject: Something
    reason: Because
    request_id: 1
    self_link: http://localhost:9001/3.0/lists/ant.example.com/held/1
    sender: anne@example.com
    subject: Something

The held message can be discarded.

    >>> dump_json(url(request_id), {
    ...     'action': 'discard',
    ...     })
    content-length: 0
    date: ...
    server: ...
    status: 204

Messages can also be accepted via the REST API.  Let's hold a new message for
moderation.
::

    >>> del msg['message-id']
    >>> msg['Message-ID'] = '<bravo>'
    >>> request_id = hold_message(ant, msg)
    >>> transaction.commit()

    >>> results = call_http(url(request_id))
    >>> print(results['message_id'])
    <bravo>

    >>> dump_json(url(request_id), {
    ...     'action': 'accept',
    ...     })
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> from mailman.testing.helpers import get_queue_messages
    >>> messages = get_queue_messages('pipeline')
    >>> len(messages)
    1
    >>> print(messages[0].msg['message-id'])
    <bravo>

Messages can be rejected via the REST API too.  These bounce the message back
to the original author.
::

    >>> del msg['message-id']
    >>> msg['Message-ID'] = '<charlie>'
    >>> request_id = hold_message(ant, msg)
    >>> transaction.commit()

    >>> results = call_http(url(request_id))
    >>> print(results['message_id'])
    <charlie>

    >>> dump_json(url(request_id), {
    ...     'action': 'reject',
    ...     })
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> from mailman.testing.helpers import get_queue_messages
    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1
    >>> print(messages[0].msg['subject'])
    Request to mailing list "Ant" rejected

The subject of the message is decoded and the original subject is accessible
under ``original_subject``.
::

    >>> msg = message_from_string("""\
    ... From: anne@example.com
    ... To: ant@example.com
    ... Subject: =?iso-8859-1?q?p=F6stal?=
    ... Message-ID: <beta>
    ...
    ... Something else.
    ... """)

    >>> from mailman.app.moderator import hold_message
    >>> request_id = hold_message(ant, msg, {'extra': 7}, 'Because')
    >>> transaction.commit()

    >>> results = call_http(url(request_id))
    >>> print(results['subject'])
    pöstal
    >>> print(results['original_subject'])
    =?iso-8859-1?q?p=F6stal?=

