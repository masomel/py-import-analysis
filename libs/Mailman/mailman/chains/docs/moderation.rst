==========
Moderation
==========

Posts by members and nonmembers are subject to moderation checks during
incoming processing.  Different situations can cause such posts to be held for
moderator approval.

    >>> mlist = create_list('test@example.com')

Members and nonmembers have a *moderation action* which can shortcut the
normal moderation checks.  The built-in chain does just a few checks first,
such as seeing if the message has a matching `Approved:` header, or if the
emergency flag has been set on the mailing list, or whether a mail loop has
been detected.

Mailing lists have a default moderation action, one for members and another
for nonmembers.  If a member's moderation action is ``None``, then the member
moderation check falls back to the appropriate list default.

A moderation action of `defer` means that no explicit moderation check is
performed and the rest of the rule chain processing proceeds as normal.  But
it is also common for first-time posters to have a `hold` action, meaning that
their messages are held for moderator approval for a while.

Nonmembers almost always have a `hold` action, though some mailing lists may
choose to set this default action to `discard`, meaning their posts would be
immediately thrown away.


Member moderation
=================

Posts by list members are moderated if the member's moderation action is not
deferred.  The default setting for the moderation action of new members is
determined by the mailing list's settings.  By default, a mailing list is not
set to moderate new member postings.

    >>> print(mlist.default_member_action)
    Action.defer

In order to find out whether the message is held or accepted, we can subscribe
to internal events that are triggered on each case.

    >>> from mailman.interfaces.chain import ChainEvent
    >>> def on_chain(event):
    ...     if isinstance(event, ChainEvent):
    ...         print(event)
    ...         print(event.chain)
    ...         print('Subject:', event.msg['subject'])
    ...         print('Hits:')
    ...         for hit in event.msgdata.get('rule_hits', []):
    ...             print('   ', hit)
    ...         print('Misses:')
    ...         for miss in event.msgdata.get('rule_misses', []):
    ...             print('   ', miss)

Anne is a list member with moderation action of ``None`` so that moderation
will fall back to the mailing list's ``default_member_action``.

    >>> from mailman.testing.helpers import subscribe
    >>> member = subscribe(mlist, 'Anne', email='anne@example.com')
    >>> member
    <Member: Anne Person <anne@example.com> on test@example.com
             as MemberRole.member>
    >>> print(member.moderation_action)
    None

Anne's post to the mailing list runs through the incoming runner's default
built-in chain.  No rules hit and so the message is accepted.
::

    >>> msg = message_from_string("""\
    ... From: anne@example.com
    ... To: test@example.com
    ... Subject: aardvark
    ...
    ... This is a test.
    ... """)

    >>> from mailman.core.chains import process
    >>> from mailman.testing.helpers import event_subscribers
    >>> with event_subscribers(on_chain):
    ...     process(mlist, msg, {}, 'default-posting-chain')
    <mailman.interfaces.chain.AcceptEvent ...>
    <mailman.chains.accept.AcceptChain ...>
    Subject: aardvark
    Hits:
    Misses:
        dmarc-mitigation
        approved
        emergency
        loop
        banned-address
        member-moderation
        nonmember-moderation
        administrivia
        implicit-dest
        max-recipients
        max-size
        news-moderation
        no-subject
        suspicious-header

However, when Anne's moderation action is set to `hold`, her post is held for
moderator approval.
::

    >>> from mailman.interfaces.action import Action
    >>> member.moderation_action = Action.hold

    >>> msg = message_from_string("""\
    ... From: anne@example.com
    ... To: test@example.com
    ... Subject: badger
    ...
    ... This is a test.
    ... """)

    >>> with event_subscribers(on_chain):
    ...     process(mlist, msg, {}, 'default-posting-chain')
    <mailman.interfaces.chain.HoldEvent ...>
    <mailman.chains.hold.HoldChain ...>
    Subject: badger
    Hits:
        member-moderation
    Misses:
        dmarc-mitigation
        approved
        emergency
        loop
        banned-address

Anne's moderation action can also be set to `discard`...
::

    >>> member.moderation_action = Action.discard

    >>> msg = message_from_string("""\
    ... From: anne@example.com
    ... To: test@example.com
    ... Subject: cougar
    ...
    ... This is a test.
    ... """)

    >>> with event_subscribers(on_chain):
    ...     process(mlist, msg, {}, 'default-posting-chain')
    <mailman.interfaces.chain.DiscardEvent ...>
    <mailman.chains.discard.DiscardChain ...>
    Subject: cougar
    Hits:
        member-moderation
    Misses:
        dmarc-mitigation
        approved
        emergency
        loop
        banned-address

... or `reject`.

    >>> member.moderation_action = Action.reject

    >>> msg = message_from_string("""\
    ... From: anne@example.com
    ... To: test@example.com
    ... Subject: dingo
    ...
    ... This is a test.
    ... """)

    >>> with event_subscribers(on_chain):
    ...     process(mlist, msg, {}, 'default-posting-chain')
    <mailman.interfaces.chain.RejectEvent ...>
    <mailman.chains.reject.RejectChain ...>
    Subject: dingo
    Hits:
        member-moderation
    Misses:
        dmarc-mitigation
        approved
        emergency
        loop
        banned-address


Nonmembers
==========

Registered nonmembers are handled very similarly to members, except that a
different list default setting is used when moderating nonmemberds.  This is
how the incoming runner adds sender addresses as nonmembers.

    >>> from zope.component import getUtility
    >>> from mailman.interfaces.usermanager import IUserManager
    >>> user_manager = getUtility(IUserManager)
    >>> address = user_manager.create_address('bart@example.com')
    >>> address
    <Address: bart@example.com [not verified] at ...>

When the moderation rule runs on a message from this sender, this address will
be registered as a nonmember of the mailing list, and it will be held for
moderator approval.
::

    >>> msg = message_from_string("""\
    ... From: bart@example.com
    ... To: test@example.com
    ... Subject: elephant
    ...
    ... """)

    >>> with event_subscribers(on_chain):
    ...     process(mlist, msg, {}, 'default-posting-chain')
    <mailman.interfaces.chain.HoldEvent ...>
    <mailman.chains.hold.HoldChain ...>
    Subject: elephant
    Hits:
        nonmember-moderation
    Misses:
        dmarc-mitigation
        approved
        emergency
        loop
        banned-address
        member-moderation

    >>> nonmember = mlist.nonmembers.get_member('bart@example.com')
    >>> nonmember
    <Member: bart@example.com on test@example.com as MemberRole.nonmember>

When a nonmember's default moderation action is ``None``, the rule will use
the mailing list's ``default_nonmember_action``.

    >>> print(nonmember.moderation_action)
    None
    >>> print(mlist.default_nonmember_action)
    Action.hold
