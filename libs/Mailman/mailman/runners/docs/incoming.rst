===================
The incoming runner
===================

This runner's sole purpose in life is to decide the disposition of the
message.  It can either be accepted for delivery, rejected (i.e. bounced),
held for moderator approval, or discarded.

The runner operates by processing chains on a message/metadata pair in the
context of a mailing list.  Each mailing list has a default chain for messages
posted to the mailing list.  This chain is processed with the message
eventually ending up in one of the four disposition states described above.

    >>> mlist = create_list('test@example.com')
    >>> print(mlist.posting_chain)
    default-posting-chain


Sender addresses
================

The incoming runner ensures that the sender addresses on the message are
registered with the system.  This is used for determining nonmember posting
privileges.  The addresses will not be linked to a user and will be
unverified, so if the real user comes along later and claims the address, it
will be linked to their user account (and must be verified).

While configurable, the *sender addresses* by default are those named in the
`From:`, `Sender:`, and `Reply-To:` headers, as well as the envelope sender
(though we won't worry about the latter).
::

    >>> msg = message_from_string("""\
    ... From: zperson@example.com
    ... Reply-To: yperson@example.com
    ... Sender: xperson@example.com
    ... To: test@example.com
    ... Subject: This is spiced ham
    ... Message-ID: <bogus>
    ...
    ... """)

    >>> from zope.component import getUtility
    >>> from mailman.interfaces.usermanager import IUserManager
    >>> user_manager = getUtility(IUserManager)
    >>> print(user_manager.get_address('xperson@example.com'))
    None
    >>> print(user_manager.get_address('yperson@example.com'))
    None
    >>> print(user_manager.get_address('zperson@example.com'))
    None

Inject the message into the incoming queue, similar to the way the upstream
mail server normally would.

    >>> from mailman.app.inject import inject_message
    >>> filebase = inject_message(mlist, msg)

The incoming runner runs until it is empty.

    >>> from mailman.runners.incoming import IncomingRunner
    >>> from mailman.testing.helpers import make_testable_runner
    >>> incoming = make_testable_runner(IncomingRunner, 'in')
    >>> incoming.run()

And now the addresses are known to the system.  As mentioned above, they are
not linked to a user and are unverified.

    >>> for localpart in ('xperson', 'yperson', 'zperson'):
    ...     email = '{0}@example.com'.format(localpart)
    ...     address = user_manager.get_address(email)
    ...     print('{0}; verified? {1}; user? {2}'.format(
    ...           address.email,
    ...           ('No' if address.verified_on is None else 'Yes'),
    ...           user_manager.get_user(email)))
    xperson@example.com; verified? No; user? None
    yperson@example.com; verified? No; user? None
    zperson@example.com; verified? No; user? None

..
    Clear the pipeline queue of artifacts that affect the following tests.
    >>> from mailman.testing.helpers import get_queue_messages
    >>> ignore = get_queue_messages('pipeline')


Accepted messages
=================

We have a message that is going to be sent to the mailing list.  Once Anne is
a member of the mailing list, this message is so perfectly fine for posting
that it will be accepted and forward to the pipeline queue.
::

    >>> from mailman.testing.helpers import subscribe
    >>> subscribe(mlist, 'Anne')
    <Member: Anne Person <aperson@example.com> on test@example.com
             as MemberRole.member>

    >>> msg = message_from_string("""\
    ... From: aperson@example.com
    ... To: test@example.com
    ... Subject: My first post
    ... Message-ID: <first>
    ...
    ... First post!
    ... """)

Inject the message into the incoming queue and run until the queue is empty.

    >>> filebase = inject_message(mlist, msg)
    >>> incoming.run()

There are no messages left in the incoming queue.

    >>> get_queue_messages('in')
    []

Now the message is in the pipeline queue.

    >>> messages = get_queue_messages('pipeline')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    From: aperson@example.com
    To: test@example.com
    Subject: My first post
    Message-ID: <first>
    Message-ID-Hash: 4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB
    X-Message-ID-Hash: 4CMWUN6BHVCMHMDAOSJZ2Q72G5M32MWB
    Date: ...
    X-Mailman-Rule-Misses: dmarc-mitigation; approved; emergency; loop;
        banned-address; member-moderation; nonmember-moderation; administrivia;
        implicit-dest; max-recipients; max-size; news-moderation; no-subject;
        suspicious-header
    <BLANKLINE>
    First post!
    <BLANKLINE>
    >>> dump_msgdata(messages[0].msgdata)
    _parsemsg    : False
    envsender    : noreply@example.com
    ...


Held messages
=============

The list moderator sets the emergency flag on the mailing list.  The built-in
chain will now hold all posted messages, so nothing will show up in the
pipeline queue.
::

    >>> from mailman.interfaces.chain import ChainEvent
    >>> def on_chain(event):
    ...     if isinstance(event, ChainEvent):
    ...         print(event)
    ...         print(event.chain)
    ...         print('From: {0}\nTo: {1}\nMessage-ID: {2}'.format(
    ...             event.msg['from'], event.msg['to'],
    ...             event.msg['message-id']))

    >>> mlist.emergency = True

    >>> from mailman.testing.helpers import event_subscribers
    >>> with event_subscribers(on_chain):
    ...     filebase = inject_message(mlist, msg)
    ...     incoming.run()
    <mailman.interfaces.chain.HoldEvent ...>
    <mailman.chains.hold.HoldChain ...>
    From: aperson@example.com
    To: test@example.com
    Message-ID: <first>

    >>> mlist.emergency = False


Discarded messages
==================

Another possibility is that the message would get immediately discarded.  The
built-in chain does not have such a disposition by default, so let's craft a
new chain and set it as the mailing list's start chain.
::

    >>> from mailman.chains.base import Chain, Link
    >>> from mailman.interfaces.chain import LinkAction
    >>> def make_chain(name, target_chain):
    ...     test_chain = Chain(name, 'Testing {}'.format(target_chain))
    ...     config.chains[test_chain.name] = test_chain
    ...     link = Link('truth', LinkAction.jump, target_chain)
    ...     test_chain.append_link(link)
    ...     return test_chain

    >>> test_chain = make_chain('always-discard', 'discard')
    >>> mlist.posting_chain = test_chain.name

    >>> msg.replace_header('message-id', '<second>')
    >>> with event_subscribers(on_chain):
    ...     filebase = inject_message(mlist, msg)
    ...     incoming.run()
    <mailman.interfaces.chain.DiscardEvent ...>
    <mailman.chains.discard.DiscardChain ...>
    From: aperson@example.com
    To: test@example.com
    Message-ID: <second>

    >>> del config.chains[test_chain.name]

..
    The virgin queue needs to be cleared out due to artifacts from the
    previous tests above.

    >>> ignore = get_queue_messages('virgin')


Rejected messages
=================

Similar to discarded messages, a message can be rejected, or bounced back to
the original sender.  Again, the built-in chain doesn't support this so we'll
just create a new chain that does.

    >>> test_chain = make_chain('always-reject', 'reject')
    >>> mlist.posting_chain = test_chain.name

    >>> msg.replace_header('message-id', '<third>')
    >>> with event_subscribers(on_chain):
    ...     filebase = inject_message(mlist, msg)
    ...     incoming.run()
    <mailman.interfaces.chain.RejectEvent ...>
    <mailman.chains.reject.RejectChain ...>
    From: aperson@example.com
    To: test@example.com
    Message-ID: <third>

The rejection message is sitting in the virgin queue waiting to be delivered
to the original sender.

    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    Subject: My first post
    From: test-owner@example.com
    To: aperson@example.com
    ...
    <BLANKLINE>
    --===============...
    Content-Type: text/plain; charset="us-ascii"
    MIME-Version: 1.0
    Content-Transfer-Encoding: 7bit
    <BLANKLINE>
    [No bounce details are available]
    --===============...
    Content-Type: message/rfc822
    MIME-Version: 1.0
    <BLANKLINE>
    From: aperson@example.com
    To: test@example.com
    Subject: My first post
    Message-ID: <third>
    Date: ...
    <BLANKLINE>
    First post!
    <BLANKLINE>
    --===============...

    >>> del config.chains['always-reject']
