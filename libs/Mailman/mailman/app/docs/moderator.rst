.. _app-moderator:

============================
Application level moderation
============================

At an application level, moderation involves holding messages and membership
changes for moderator approval.  This utilizes the :ref:`lower level interface
<model-requests>` for list-centric moderation requests.

Moderation is always mailing list-centric.

    >>> mlist = create_list('ant@example.com')
    >>> mlist.preferred_language = 'en'
    >>> mlist.display_name = 'A Test List'
    >>> mlist.admin_immed_notify = False

We'll use the lower level API for diagnostic purposes.

    >>> from mailman.interfaces.requests import IListRequests
    >>> requests = IListRequests(mlist)


Message moderation
==================

Holding messages
----------------

Anne posts a message to the mailing list, but she is not a member of the list,
so the message is held for moderator approval.

    >>> msg = message_from_string("""\
    ... From: anne@example.org
    ... To: ant@example.com
    ... Subject: Something important
    ... Message-ID: <aardvark>
    ...
    ... Here's something important about our mailing list.
    ... """)

*Holding a message* means keeping a copy of it that a moderator must approve
before the message is posted to the mailing list.  To hold the message, the
message, its metadata, and a reason for the hold must be provided.  In this
case, we won't include any additional metadata.

    >>> from mailman.app.moderator import hold_message
    >>> hold_message(mlist, msg, {}, 'Needs approval')
    1

We can also hold a message with some additional metadata.
::

    >>> msg = message_from_string("""\
    ... From: bart@example.org
    ... To: ant@example.com
    ... Subject: Something important
    ... Message-ID: <badger>
    ...
    ... Here's something important about our mailing list.
    ... """)
    >>> msgdata = dict(sender='anne@example.com', approved=True)

    >>> hold_message(mlist, msg, msgdata, 'Feeling ornery')
    2


Disposing of messages
---------------------

The moderator can select one of several dispositions:

  * discard - throw the message away.
  * reject - bounces the message back to the original author.
  * defer - defer any action on the message (continue to hold it)
  * accept - accept the message for posting.

The most trivial is to simply defer a decision for now.

    >>> from mailman.interfaces.action import Action
    >>> from mailman.app.moderator import handle_message
    >>> handle_message(mlist, 1, Action.defer)

This leaves the message in the requests database.

    >>> key, data = requests.get_request(1)
    >>> print(key)
    <aardvark>

The moderator can also discard the message.

    >>> handle_message(mlist, 1, Action.discard)
    >>> print(requests.get_request(1))
    None

The message can be rejected, which bounces the message back to the original
sender.

    >>> handle_message(mlist, 2, Action.reject, 'Off topic')

The message is no longer available in the requests database.

    >>> print(requests.get_request(2))
    None

And there is one message in the *virgin* queue - the rejection notice.

    >>> from mailman.testing.helpers import get_queue_messages
    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    MIME-Version: 1.0
    ...
    Subject: Request to mailing list "A Test List" rejected
    From: ant-bounces@example.com
    To: bart@example.org
    ...
    <BLANKLINE>
    Your request to the ant@example.com mailing list
    <BLANKLINE>
        Posting of your message titled "Something important"
    <BLANKLINE>
    has been rejected by the list moderator.  The moderator gave the
    following reason for rejecting your request:
    <BLANKLINE>
    "Off topic"
    <BLANKLINE>
    Any questions or comments should be directed to the list administrator
    at:
    <BLANKLINE>
        ant-owner@example.com
    <BLANKLINE>

The bounce gets sent to the original sender.

    >>> for recipient in sorted(messages[0].msgdata['recipients']):
    ...     print(recipient)
    bart@example.org

Or the message can be approved.

    >>> msg = message_from_string("""\
    ... From: cris@example.org
    ... To: ant@example.com
    ... Subject: Something important
    ... Message-ID: <caribou>
    ...
    ... Here's something important about our mailing list.
    ... """)
    >>> id = hold_message(mlist, msg, {}, 'Needs approval')
    >>> handle_message(mlist, id, Action.accept)

This places the message back into the incoming queue for further processing,
however the message metadata indicates that the message has been approved.
::

    >>> messages = get_queue_messages('pipeline')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    From: cris@example.org
    To: ant@example.com
    Subject: Something important
    ...

    >>> dump_msgdata(messages[0].msgdata)
    _parsemsg         : False
    approved          : True
    moderator_approved: True
    type              : data
    version           : 3


Forwarding the message
----------------------

The message can be forwarded to another address.  This is helpful for getting
the message into the inbox of one of the moderators.
::

    >>> msg = message_from_string("""\
    ... From: elly@example.org
    ... To: ant@example.com
    ... Subject: Something important
    ... Message-ID: <elephant>
    ...
    ... Here's something important about our mailing list.
    ... """)
    >>> req_id = hold_message(mlist, msg, {}, 'Needs approval')
    >>> handle_message(mlist, req_id, Action.discard,
    ...                forward=['zack@example.com'])

The forwarded message is in the virgin queue, destined for the moderator.
::

    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    Subject: Forward of moderated message
    From: ant-bounces@example.com
    To: zack@example.com
    ...

    >>> for recipient in sorted(messages[0].msgdata['recipients']):
    ...     print(recipient)
    zack@example.com


Holding unsubscription requests
===============================

Some lists require moderator approval for unsubscriptions.  In this case, only
the unsubscribing address is required.

Fred is a member of the mailing list...

    >>> from mailman.interfaces.usermanager import IUserManager
    >>> from zope.component import getUtility
    >>> mlist.send_welcome_message = False
    >>> fred = getUtility(IUserManager).create_address(
    ...     'fred@example.com', 'Fred Person')
    >>> from mailman.interfaces.subscriptions import ISubscriptionManager
    >>> registrar = ISubscriptionManager(mlist)
    >>> token, token_owner, member = registrar.register(
    ...     fred, pre_verified=True, pre_confirmed=True, pre_approved=True)
    >>> member
    <Member: Fred Person <fred@example.com> on ant@example.com
             as MemberRole.member>

...but now that he wants to leave the mailing list, his request must be
approved.

    >>> from mailman.app.moderator import hold_unsubscription
    >>> req_id = hold_unsubscription(mlist, 'fred@example.com')

As with subscription requests, the unsubscription request can be deferred.

    >>> from mailman.app.moderator import handle_unsubscription
    >>> handle_unsubscription(mlist, req_id, Action.defer)
    >>> print(mlist.members.get_member('fred@example.com').address)
    Fred Person <fred@example.com>

The held unsubscription can also be discarded, and the member will remain
subscribed.

    >>> handle_unsubscription(mlist, req_id, Action.discard)
    >>> print(mlist.members.get_member('fred@example.com').address)
    Fred Person <fred@example.com>

The request can be rejected, in which case a message is sent to the member,
and the person remains a member of the mailing list.

    >>> req_id = hold_unsubscription(mlist, 'fred@example.com')
    >>> handle_unsubscription(mlist, req_id, Action.reject, 'No can do')
    >>> print(mlist.members.get_member('fred@example.com').address)
    Fred Person <fred@example.com>

Fred gets a rejection notice.
::

    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1

    >>> print(messages[0].msg.as_string())
    MIME-Version: 1.0
    ...
    Subject: Request to mailing list "A Test List" rejected
    From: ant-bounces@example.com
    To: fred@example.com
    ...
    Your request to the ant@example.com mailing list
    <BLANKLINE>
        Unsubscription request
    <BLANKLINE>
    has been rejected by the list moderator.  The moderator gave the
    following reason for rejecting your request:
    <BLANKLINE>
    "No can do"
    ...

The unsubscription request can also be accepted.  This removes the member from
the mailing list.

    >>> req_id = hold_unsubscription(mlist, 'fred@example.com')
    >>> mlist.send_goodbye_message = False
    >>> handle_unsubscription(mlist, req_id, Action.accept)
    >>> print(mlist.members.get_member('fred@example.com'))
    None


Notifications
=============

Membership change requests
--------------------------

Usually, the list administrators want to be notified when there are membership
change requests they need to moderate.  These notifications are sent when the
list is configured to send them.

    >>> from mailman.interfaces.mailinglist import SubscriptionPolicy
    >>> mlist.admin_immed_notify = True
    >>> mlist.subscription_policy = SubscriptionPolicy.moderate

Gwen tries to subscribe to the mailing list.

    >>> gwen = getUtility(IUserManager).create_address(
    ...     'gwen@example.com', 'Gwen Person')
    >>> token, token_owner, member = registrar.register(
    ...     gwen, pre_verified=True, pre_confirmed=True)

Her subscription must be approved by the list administrator, so she is not yet
a member of the mailing list.

    >>> print(member)
    None
    >>> print(mlist.members.get_member('gwen@example.com'))
    None

There's now a message in the virgin queue, destined for the list owner.

    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    MIME-Version: 1.0
    ...
    Subject: New subscription request to A Test List from gwen@example.com
    From: ant-owner@example.com
    To: ant-owner@example.com
    ...
    Your authorization is required for a mailing list subscription request
    approval:
    <BLANKLINE>
        For:  Gwen Person <gwen@example.com>
        List: ant@example.com

Similarly, the administrator gets notifications on unsubscription requests.
Jeff is a member of the mailing list, and chooses to unsubscribe.

    >>> unsub_req_id = hold_unsubscription(mlist, 'jeff@example.org')
    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    MIME-Version: 1.0
    ...
    Subject: New unsubscription request from A Test List by jeff@example.org
    From: ant-owner@example.com
    To: ant-owner@example.com
    ...
    Your authorization is required for a mailing list unsubscription
    request approval:
    <BLANKLINE>
        For:  jeff@example.org
        List: ant@example.com
    <BLANKLINE>


Membership changes
------------------

When a new member request is accepted, the mailing list administrators can
receive a membership change notice.

    >>> mlist.admin_notify_mchanges = True
    >>> mlist.admin_immed_notify = False
    >>> token, token_owner, member = registrar.confirm(token)
    >>> member
    <Member: Gwen Person <gwen@example.com> on ant@example.com
             as MemberRole.member>
    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    MIME-Version: 1.0
    ...
    Subject: A Test List subscription notification
    From: noreply@example.com
    To: ant-owner@example.com
    ...
    Gwen Person <gwen@example.com> has been successfully subscribed to A
    Test List.

Similarly when an unsubscription request is accepted, the administrators can
get a notification.

    >>> req_id = hold_unsubscription(mlist, 'gwen@example.com')
    >>> handle_unsubscription(mlist, req_id, Action.accept)
    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    MIME-Version: 1.0
    ...
    Subject: A Test List unsubscription notification
    From: noreply@example.com
    To: ant-owner@example.com
    ...
    Gwen Person <gwen@example.com> has been removed from A Test List.


Welcome messages
----------------

When a member is subscribed to the mailing list, they can get a welcome
message.

    >>> mlist.admin_notify_mchanges = False
    >>> mlist.send_welcome_message = True
    >>> herb = getUtility(IUserManager).create_address(
    ...     'herb@example.com', 'Herb Person')
    >>> token, token_owner, member = registrar.register(
    ...     herb, pre_verified=True, pre_confirmed=True, pre_approved=True)
    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    MIME-Version: 1.0
    ...
    Subject: Welcome to the "A Test List" mailing list
    From: ant-request@example.com
    To: Herb Person <herb@example.com>
    ...
    Welcome to the "A Test List" mailing list!
    ...


Goodbye messages
----------------

Similarly, when the member's unsubscription request is approved, she'll get a
goodbye message.

    >>> mlist.send_goodbye_message = True
    >>> req_id = hold_unsubscription(mlist, 'herb@example.com')
    >>> handle_unsubscription(mlist, req_id, Action.accept)
    >>> messages = get_queue_messages('virgin')
    >>> len(messages)
    1
    >>> print(messages[0].msg.as_string())
    MIME-Version: 1.0
    ...
    Subject: You have been unsubscribed from the A Test List mailing list
    From: ant-bounces@example.com
    To: herb@example.com
    ...
