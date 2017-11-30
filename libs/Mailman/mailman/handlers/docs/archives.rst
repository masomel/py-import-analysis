========
Archives
========

Updating the archives with posted messages is handled by a separate queue,
which allows for better memory management and prevents blocking the main
delivery processes while messages are archived.  This also allows external
archivers to work in a separate process from the main Mailman delivery
processes.

    >>> handler = config.handlers['to-archive']
    >>> mlist = create_list('_xtest@example.com')
    >>> switchboard = config.switchboards['archive']

A helper function.

    >>> def clear():
    ...     for filebase in switchboard.files:
    ...         msg, msgdata = switchboard.dequeue(filebase)
    ...         switchboard.finish(filebase)

The purpose of this handler is to make a simple decision as to whether the
message should get archived and if so, to drop the message in the archiving
queue.  Really the most important things are to determine when a message
should *not* get archived.

For example, no digests should ever get archived.

    >>> from mailman.interfaces.archiver import ArchivePolicy
    >>> mlist.archive_policy = ArchivePolicy.public
    >>> msg = message_from_string("""\
    ... Subject: A sample message
    ...
    ... A message of great import.
    ... """)
    >>> handler.process(mlist, msg, dict(isdigest=True))
    >>> switchboard.files
    []

If the mailing list is not configured to archive, then even regular deliveries
won't be archived.

    >>> mlist.archive_policy = ArchivePolicy.never
    >>> handler.process(mlist, msg, {})
    >>> switchboard.files
    []

There are two de-facto standards for a message to indicate that it does not
want to be archived.  We've seen both in the wild so both are supported.  The
``X-No-Archive:`` header can be used to indicate that the message should not
be archived.  Confusingly, this header's value is actually ignored.

    >>> mlist.archive_policy = ArchivePolicy.public
    >>> msg = message_from_string("""\
    ... Subject: A sample message
    ... X-No-Archive: YES
    ...
    ... A message of great import.
    ... """)
    >>> handler.process(mlist, msg, dict(isdigest=True))
    >>> switchboard.files
    []

Even a ``no`` value will stop the archiving of the message.

    >>> msg = message_from_string("""\
    ... Subject: A sample message
    ... X-No-Archive: No
    ...
    ... A message of great import.
    ... """)
    >>> handler.process(mlist, msg, dict(isdigest=True))
    >>> switchboard.files
    []

Another header that's been observed is the ``X-Archive:`` header.  Here, the
header's case folded value must be ``no`` in order to prevent archiving.

    >>> msg = message_from_string("""\
    ... Subject: A sample message
    ... X-Archive: No
    ...
    ... A message of great import.
    ... """)
    >>> handler.process(mlist, msg, dict(isdigest=True))
    >>> switchboard.files
    []

But if the value is ``yes``, then the message will be archived.

    >>> msg = message_from_string("""\
    ... Subject: A sample message
    ... X-Archive: Yes
    ...
    ... A message of great import.
    ... """)
    >>> handler.process(mlist, msg, {})
    >>> len(switchboard.files)
    1
    >>> filebase = switchboard.files[0]
    >>> qmsg, qdata = switchboard.dequeue(filebase)
    >>> switchboard.finish(filebase)
    >>> print(qmsg.as_string())
    Subject: A sample message
    X-Archive: Yes
    <BLANKLINE>
    A message of great import.
    <BLANKLINE>
    >>> dump_msgdata(qdata)
    _parsemsg: False
    version  : 3

Without either archiving header, and all other things being the same, the
message will get archived.

    >>> msg = message_from_string("""\
    ... Subject: A sample message
    ...
    ... A message of great import.
    ... """)
    >>> handler.process(mlist, msg, {})
    >>> len(switchboard.files)
    1
    >>> filebase = switchboard.files[0]
    >>> qmsg, qdata = switchboard.dequeue(filebase)
    >>> switchboard.finish(filebase)
    >>> print(qmsg.as_string())
    Subject: A sample message
    <BLANKLINE>
    A message of great import.
    <BLANKLINE>
    >>> dump_msgdata(qdata)
    _parsemsg: False
    version  : 3
