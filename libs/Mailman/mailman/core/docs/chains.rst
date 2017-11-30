======
Chains
======

When a new message is posted to a mailing list, Mailman uses a set of rule
chains to decide whether the message gets accepted for posting, rejected,
discarded, or held for moderator approval.

There are a number of built-in chains available that act as end-points in the
processing of messages.


The Discard chain
=================

The `discard` chain simply throws the message away.
::

    >>> chain = config.chains['discard']
    >>> print(chain.name)
    discard
    >>> print(chain.description)
    Discard a message and stop processing.

    >>> mlist = create_list('test@example.com')
    >>> msg = message_from_string("""\
    ... From: aperson@example.com
    ... To: test@example.com
    ... Subject: My first post
    ... Message-ID: <first>
    ...
    ... An important message.
    ... """)

    >>> def print_msgid(event):
    ...     print('{0}: {1}'.format(
    ...         event.chain.name.upper(), event.msg.get('message-id', 'n/a')))

    >>> from mailman.core.chains import process
    >>> from mailman.testing.helpers import event_subscribers

    >>> with event_subscribers(print_msgid):
    ...     process(mlist, msg, {}, 'discard')
    DISCARD: <first>


The Reject chain
================

The `reject` chain bounces the message back to the original sender, and logs
this action.
::

    >>> chain = config.chains['reject']
    >>> print(chain.name)
    reject
    >>> print(chain.description)
    Reject/bounce a message and stop processing.

    >>> with event_subscribers(print_msgid):
    ...     process(mlist, msg, {}, 'reject')
    REJECT: <first>

The bounce message is now sitting in the `virgin` queue.

    >>> from mailman.testing.helpers import get_queue_messages
    >>> qfiles = get_queue_messages('virgin')
    >>> len(qfiles)
    1
    >>> print(qfiles[0].msg.as_string())
    Subject: My first post
    From: test-owner@example.com
    To: aperson@example.com
    ...
    [No bounce details are available]
    ...
    Content-Type: message/rfc822
    MIME-Version: 1.0
    <BLANKLINE>
    From: aperson@example.com
    To: test@example.com
    Subject: My first post
    Message-ID: <first>
    <BLANKLINE>
    An important message.
    <BLANKLINE>
    ...


The Hold Chain
==============

The `hold` chain places the message into the administrative request database
and depending on the list's settings, sends a notification to both the
original sender and the list moderators.  ::

    >>> chain = config.chains['hold']
    >>> print(chain.name)
    hold
    >>> print(chain.description)
    Hold a message and stop processing.

    >>> with event_subscribers(print_msgid):
    ...     process(mlist, msg, {}, 'hold')
    HOLD: <first>

There are now two messages in the virgin queue, one to the list moderators and
one to the original author.

    >>> qfiles = get_queue_messages('virgin', sort_on='to')
    >>> len(qfiles)
    2

One of the message is addressed to the mailing list moderators, and the other
is addressed to the original sender.

    >>> from operator import itemgetter
    >>> messages = sorted((item.msg for item in qfiles),
    ...                   key=itemgetter('to'), reverse=True)

This one is addressed to the list moderators.

    >>> print(messages[0].as_string())
    Subject: test@example.com post from aperson@example.com requires approval
    From: test-owner@example.com
    To: test-owner@example.com
    MIME-Version: 1.0
    ...
    As list administrator, your authorization is requested for the
    following mailing list posting:
    <BLANKLINE>
        List:    test@example.com
        From:    aperson@example.com
        Subject: My first post
    <BLANKLINE>
    The message is being held because:
    <BLANKLINE>
        N/A
    At your convenience, visit your dashboard to approve or deny the
    request.
    <BLANKLINE>
    ...
    Content-Type: message/rfc822
    MIME-Version: 1.0
    <BLANKLINE>
    From: aperson@example.com
    To: test@example.com
    Subject: My first post
    Message-ID: <first>
    Message-ID-Hash: 4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB
    X-Message-ID-Hash: 4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB
    <BLANKLINE>
    An important message.
    <BLANKLINE>
    ...
    Content-Type: message/rfc822
    MIME-Version: 1.0
    <BLANKLINE>
    Content-Type: text/plain; charset="us-ascii"
    MIME-Version: 1.0
    Content-Transfer-Encoding: 7bit
    Subject: confirm ...
    From: test-request@example.com
    ...
    <BLANKLINE>
    If you reply to this message, keeping the Subject: header intact,
    Mailman will discard the held message.  Do this if the message is
    spam.  If you reply to this message and include an Approved: header
    with the list password in it, the message will be approved for posting
    to the list.  The Approved: header can also appear in the first line
    of the body of the reply.
    ...

This message is addressed to the sender of the message.

    >>> print(messages[1].as_string())
    MIME-Version: 1.0
    Content-Type: text/plain; charset="us-ascii"
    Content-Transfer-Encoding: 7bit
    Subject: Your message to test@example.com awaits moderator approval
    From: test-bounces@example.com
    To: aperson@example.com
    ...
    Your mail to 'test@example.com' with the subject
    <BLANKLINE>
        My first post
    <BLANKLINE>
    Is being held until the list moderator can review it for approval.
    <BLANKLINE>
    The message is being held because:
    <BLANKLINE>
        N/A
    <BLANKLINE>
    Either the message will get posted to the list, or you will receive
    notification of the moderator's decision.


The Accept chain
================

The `accept` chain sends the message on the `pipeline` queue, where it will be
processed and sent on to the list membership.
::

    >>> chain = config.chains['accept']
    >>> print(chain.name)
    accept
    >>> print(chain.description)
    Accept a message.

    >>> with event_subscribers(print_msgid):
    ...     process(mlist, msg, {}, 'accept')
    ACCEPT: <first>

    >>> qfiles = get_queue_messages('pipeline')
    >>> len(qfiles)
    1
    >>> print(qfiles[0].msg.as_string())
    From: aperson@example.com
    To: test@example.com
    Subject: My first post
    Message-ID: <first>
    Message-ID-Hash: 4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB
    X-Message-ID-Hash: 4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB
    <BLANKLINE>
    An important message.
    <BLANKLINE>


Run-time chains
===============

We can also define chains at run time, and these chains can be mutated.
Run-time chains are made up of links where each link associates both a rule
and a `jump`.  The rule is really a rule name, which is looked up when
needed.  The jump names a chain which is jumped to if the rule matches.

There is one built-in posting chain.  This is the default chain to use when no
other input chain is defined for a mailing list.  It runs through the default
rules.

    >>> chain = config.chains['default-posting-chain']
    >>> print(chain.name)
    default-posting-chain
    >>> print(chain.description)
    The built-in moderation chain.

Once the sender is a member of the mailing list, the previously created
message is innocuous enough that it should pass through all default rules.
This message will end up in the `pipeline` queue.
::

    >>> from mailman.testing.helpers import subscribe
    >>> subscribe(mlist, 'Anne')
    <Member: aperson@example.com on test@example.com as MemberRole.member>

    >>> with event_subscribers(print_msgid):
    ...     process(mlist, msg, {})
    ACCEPT: <first>

    >>> qfiles = get_queue_messages('pipeline')
    >>> len(qfiles)
    1
    >>> print(qfiles[0].msg.as_string())
    From: aperson@example.com
    To: test@example.com
    Subject: My first post
    Message-ID: <first>
    Message-ID-Hash: 4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB
    X-Message-ID-Hash: 4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB
    X-Mailman-Rule-Misses: dmarc-mitigation; approved; emergency; loop;
        banned-address; member-moderation; nonmember-moderation; administrivia;
        implicit-dest; max-recipients; max-size; news-moderation; no-subject;
        suspicious-header
    <BLANKLINE>
    An important message.
    <BLANKLINE>

In addition, the message metadata now contains lists of all rules that have
hit and all rules that have missed.

    >>> dump_list(qfiles[0].msgdata['rule_hits'])
    *Empty*
    >>> dump_list(qfiles[0].msgdata['rule_misses'])
    administrivia
    approved
    banned-address
    dmarc-mitigation
    emergency
    implicit-dest
    loop
    max-recipients
    max-size
    member-moderation
    news-moderation
    no-subject
    nonmember-moderation
    suspicious-header
