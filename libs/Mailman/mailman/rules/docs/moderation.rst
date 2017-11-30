==========
Moderation
==========

All members and nonmembers have a moderation action, which defaults to the
appropriate list's default action.  When the action is not `defer`, the
`moderation` rule flags the message as needing moderation.  This might be to
automatically accept, discard, reject, or hold the message.

Two separate rules check for member and nonmember moderation.  Member
moderation happens early in the built-in chain, while nonmember moderation
happens later in the chain, after normal moderation checks.

    >>> mlist = create_list('test@example.com')


Member moderation
=================

    >>> member_rule = config.rules['member-moderation']
    >>> print(member_rule.name)
    member-moderation

Anne, a mailing list member, sends a message to the mailing list.  Her
moderation action is not set.

    >>> from mailman.testing.helpers import subscribe
    >>> member = subscribe(mlist, 'Anne')
    >>> member
    <Member: Anne Person <aperson@example.com> on test@example.com
             as MemberRole.member>
    >>> print(member.moderation_action)
    None

Because the list's default member action is set to `defer`, Anne's posting is
not moderated.

    >>> print(mlist.default_member_action)
    Action.defer

Because Anne is not moderated, the member moderation rule does not match.

    >>> member_msg = message_from_string("""\
    ... From: aperson@example.com
    ... To: test@example.com
    ... Subject: A posted message
    ...
    ... """)
    >>> member_rule.check(mlist, member_msg, {})
    False

Once the member's moderation action is set to something other than `defer` or
``None`` (given the list's current default member moderation action), the rule
matches.  Also, the message metadata has a few extra pieces of information for
the eventual moderation chain.

    >>> from mailman.interfaces.action import Action
    >>> member.moderation_action = Action.hold
    >>> msgdata = {}
    >>> member_rule.check(mlist, member_msg, msgdata)
    True
    >>> dump_msgdata(msgdata)
    moderation_action : hold
    moderation_reasons: ['The message comes from a moderated member']
    moderation_sender : aperson@example.com


Nonmembers
==========

Nonmembers are handled in a similar way, although by default, nonmember
postings are held for moderator approval.

    >>> nonmember_rule = config.rules['nonmember-moderation']
    >>> print(nonmember_rule.name)
    nonmember-moderation

Bart, who is not a member of the mailing list, sends a message to the list.
He has no explicit nonmember moderation action.

    >>> from mailman.interfaces.member import MemberRole
    >>> nonmember = subscribe(mlist, 'Bart', MemberRole.nonmember)
    >>> nonmember
    <Member: Bart Person <bperson@example.com> on test@example.com
             as MemberRole.nonmember>
    >>> print(nonmember.moderation_action)
    None

The list's default nonmember moderation action is to hold postings by
nonmembers.

    >>> print(mlist.default_nonmember_action)
    Action.hold

Since Bart is registered as a nonmember of the list, and his moderation action
is set to None, the action falls back to the list's default nonmember
moderation action, which is to hold the post for moderator approval.  Thus the
rule matches and the message metadata again carries some useful information.

    >>> nonmember_msg = message_from_string("""\
    ... From: bperson@example.com
    ... To: test@example.com
    ... Subject: A posted message
    ...
    ... """)
    >>> msgdata = {}
    >>> nonmember_rule.check(mlist, nonmember_msg, msgdata)
    True
    >>> dump_msgdata(msgdata)
    moderation_action : hold
    moderation_reasons: ['The message is not from a list member']
    moderation_sender : bperson@example.com

Of course, the nonmember action can be set to defer the decision, in which
case the rule does not match.

    >>> nonmember.moderation_action = Action.defer
    >>> nonmember_rule.check(mlist, nonmember_msg, {})
    False


Unregistered nonmembers
=======================

The incoming runner ensures that all sender addresses are registered in the
system, but it is the moderation rule that subscribes nonmember addresses to
the mailing list if they are not already subscribed.
::

    >>> from mailman.interfaces.usermanager import IUserManager
    >>> from zope.component import getUtility
    >>> address = getUtility(IUserManager).create_address(
    ...     'cperson@example.com')
    >>> address
    <Address: cperson@example.com [not verified] at ...>

    >>> msg = message_from_string("""\
    ... From: cperson@example.com
    ... To: test@example.com
    ... Subject: A posted message
    ...
    ... """)

cperson is neither a member, nor a nonmember of the mailing list.
::

    >>> def memberkey(member):
    ...     return member.mailing_list, member.address.email, member.role.value

    >>> dump_list(mlist.members.members, key=memberkey)
    <Member: Anne Person <aperson@example.com>
             on test@example.com as MemberRole.member>
    >>> dump_list(mlist.nonmembers.members, key=memberkey)
    <Member: Bart Person <bperson@example.com>
             on test@example.com as MemberRole.nonmember>

However, when the nonmember moderation rule runs, it adds the cperson as a
nonmember of the list.  The rule also matches.

    >>> msgdata = {}
    >>> nonmember_rule.check(mlist, msg, msgdata)
    True
    >>> dump_msgdata(msgdata)
    moderation_action : hold
    moderation_reasons: ['The message is not from a list member']
    moderation_sender : cperson@example.com

    >>> dump_list(mlist.members.members, key=memberkey)
    <Member: Anne Person <aperson@example.com>
             on test@example.com as MemberRole.member>
    >>> dump_list(mlist.nonmembers.members, key=memberkey)
    <Member: Bart Person <bperson@example.com>
             on test@example.com as MemberRole.nonmember>
    <Member: cperson@example.com
             on test@example.com as MemberRole.nonmember>


Cross-membership checks
=======================

Of course, the member moderation rule does not match for nonmembers...

    >>> member_rule.check(mlist, nonmember_msg, {})
    False
    >>> nonmember_rule.check(mlist, member_msg, {})
    False
