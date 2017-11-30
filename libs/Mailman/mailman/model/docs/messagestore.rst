=================
The message store
=================

The message store is a collection of messages keyed off of ``Message-ID`` and
``X-Message-ID-Hash`` headers.  Either of these values can be combined with
the message's ``List-Archive`` header to create a globally unique URI to the
message object in the internet facing interface of the message store.  The
``X-Message-ID-Hash`` is the base-32 SHA1 hash of the ``Message-ID``.

    >>> from mailman.interfaces.messages import IMessageStore
    >>> from zope.component import getUtility
    >>> message_store = getUtility(IMessageStore)

A message with a ``Message-ID`` header can be stored.

    >>> msg = message_from_string("""\
    ... Subject: An important message
    ... Message-ID: <87myycy5eh.fsf@uwakimon.sk.tsukuba.ac.jp>
    ...
    ... This message is very important.
    ... """)
    >>> x_message_id_hash = message_store.add(msg)
    >>> print(x_message_id_hash)
    JJIGKPKB6CVDX6B2CUG4IHAJRIQIOUTP
    >>> print(msg.as_string())
    Subject: An important message
    Message-ID: <87myycy5eh.fsf@uwakimon.sk.tsukuba.ac.jp>
    Message-ID-Hash: JJIGKPKB6CVDX6B2CUG4IHAJRIQIOUTP
    X-Message-ID-Hash: JJIGKPKB6CVDX6B2CUG4IHAJRIQIOUTP
    <BLANKLINE>
    This message is very important.
    <BLANKLINE>


Finding messages
================

There are several ways to find a message given either the ``Message-ID`` or
``X-Message-ID-Hash`` headers.  In either case, if no matching message is
found, ``None`` is returned.

    >>> print(message_store.get_message_by_id('nothing'))
    None
    >>> print(message_store.get_message_by_hash('nothing'))
    None

Given an existing ``Message-ID``, the message can be found.

    >>> message = message_store.get_message_by_id(msg['message-id'])
    >>> print(message.as_string())
    Subject: An important message
    Message-ID: <87myycy5eh.fsf@uwakimon.sk.tsukuba.ac.jp>
    Message-ID-Hash: JJIGKPKB6CVDX6B2CUG4IHAJRIQIOUTP
    X-Message-ID-Hash: JJIGKPKB6CVDX6B2CUG4IHAJRIQIOUTP
    <BLANKLINE>
    This message is very important.
    <BLANKLINE>

Similarly, we can find messages by the ``X-Message-ID-Hash``:

    >>> message = message_store.get_message_by_hash(msg['x-message-id-hash'])
    >>> print(message.as_string())
    Subject: An important message
    Message-ID: <87myycy5eh.fsf@uwakimon.sk.tsukuba.ac.jp>
    Message-ID-Hash: JJIGKPKB6CVDX6B2CUG4IHAJRIQIOUTP
    X-Message-ID-Hash: JJIGKPKB6CVDX6B2CUG4IHAJRIQIOUTP
    <BLANKLINE>
    This message is very important.
    <BLANKLINE>


Iterating over all messages
===========================

The message store provides a means to iterate over all the messages it
contains.

    >>> messages = list(message_store.messages)
    >>> len(messages)
    1
    >>> print(messages[0].as_string())
    Subject: An important message
    Message-ID: <87myycy5eh.fsf@uwakimon.sk.tsukuba.ac.jp>
    Message-ID-Hash: JJIGKPKB6CVDX6B2CUG4IHAJRIQIOUTP
    X-Message-ID-Hash: JJIGKPKB6CVDX6B2CUG4IHAJRIQIOUTP
    <BLANKLINE>
    This message is very important.
    <BLANKLINE>


Deleting messages from the store
================================

You delete a message from the storage service by providing the ``Message-ID``
for the message you want to delete.

    >>> message_id = message['message-id']
    >>> message_store.delete_message(message_id)
    >>> list(message_store.messages)
    []
    >>> print(message_store.get_message_by_id(message_id))
    None
    >>> print(message_store.get_message_by_hash(message['x-message-id-hash']))
    None
