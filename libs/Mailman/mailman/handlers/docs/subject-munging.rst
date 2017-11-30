================
Subject prefixes
================

Mailing lists can define a *subject prefix* which gets added to the front of
any ``Subject`` text.  This can be used to quickly identify which mailing list
the message was posted to.

    >>> mlist = create_list('test@example.com')

The default list style gives the mailing list a default prefix.

    >>> print(mlist.subject_prefix)
    [Test]

This can be changed to anything, but typically ends with a trailing space.

    >>> mlist.subject_prefix = '[XTest] '
    >>> process = config.handlers['subject-prefix'].process


No Subject
==========

If the original message has no ``Subject``, then a canned one is used.

    >>> msg = message_from_string("""\
    ... From: aperson@example.com
    ...
    ... A message of great import.
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'])
    [XTest] (no subject)


Inserting a prefix
==================

If the original message had a ``Subject`` header, then the prefix is inserted
at the beginning of the header's value.

    >>> msg = message_from_string("""\
    ... From: aperson@example.com
    ... Subject: Something important
    ...
    ... A message of great import.
    ... """)
    >>> msgdata = {}
    >>> process(mlist, msg, msgdata)
    >>> print(msg['subject'])
    [XTest] Something important

The original ``Subject`` is available in the metadata.

    >>> print(msgdata['original_subject'])
    Something important

If a ``Subject`` header already has a prefix, usually following a ``Re:``
marker, another one will not be added but the prefix will be moved to the
front of the header text.

    >>> msg = message_from_string("""\
    ... From: aperson@example.com
    ... Subject: Re: [XTest] Something important
    ...
    ... A message of great import.
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'])
    [XTest] Re: Something important

If the ``Subject`` header has a prefix at the front of the header text, that's
where it will stay.

    >>> msg = message_from_string("""\
    ... From: aperson@example.com
    ... Subject: [XTest] Re: Something important
    ...
    ... A message of great import.
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'])
    [XTest] Re: Something important

Sometimes the incoming ``Subject`` header has a pathological sequence of
``Re:`` like markers. These should all be collapsed up to the first non-``Re:``
marker.

    >>> msg = message_from_string("""\
    ... From: aperson@example.com
    ... Subject: [XTest] Re: RE : Re: Re: Re: Re: Re: Something important
    ...
    ... A message of great import.
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'])
    [XTest] Re: Something important


Internationalized headers
=========================

Internationalization adds some interesting twists to the handling of subject
prefixes.  Part of what makes this interesting is the encoding of i18n headers
using RFC 2047, and lists whose preferred language is in a different character
set than the encoded header.

    >>> msg = message_from_string("""\
    ... Subject: =?iso-2022-jp?b?GyRCJWEhPCVrJV4lcxsoQg==?=
    ...
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'].encode())
    [XTest] =?iso-2022-jp?b?GyRCJWEhPCVrJV4lcxsoQg==?=
    >>> print(str(msg['subject']))
    [XTest] メールマン


Prefix numbers
==============

Subject prefixes support a placeholder for the numeric post id.  Every time a
message is posted to the mailing list, a *post id* gets incremented.  This is
a purely sequential integer that increases monotonically.  By added a ``%d``
placeholder to the subject prefix, this post id can be included in the prefix.

    >>> mlist.subject_prefix = '[XTest %d] '
    >>> mlist.post_id = 456
    >>> msg = message_from_string("""\
    ... Subject: Something important
    ...
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'])
    [XTest 456] Something important

This works even when the message is a reply, except that in this case, the
numeric post id in the generated subject prefix is updated with the new post
id.

    >>> msg = message_from_string("""\
    ... Subject: [XTest 123] Re: Something important
    ...
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'])
    [XTest 456] Re: Something important

If the ``Subject`` header had old style prefixing, the prefix is moved to the
front of the header text.

    >>> msg = message_from_string("""\
    ... Subject: Re: [XTest 123] Something important
    ...
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'])
    [XTest 456] Re: Something important


And of course, the proper thing is done when posting id numbers are included
in the subject prefix, and the subject is encoded non-ASCII.

    >>> msg = message_from_string("""\
    ... Subject: =?iso-2022-jp?b?GyRCJWEhPCVrJV4lcxsoQg==?=
    ...
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'].encode())
    [XTest 456] =?iso-2022-jp?b?GyRCJWEhPCVrJV4lcxsoQg==?=
    >>> print(msg['subject'])
    [XTest 456] メールマン

Even more fun is when the internationalized ``Subject`` header already has a
prefix, possibly with a different posting number.

    >>> msg = message_from_string("""\
    ... Subject: [XTest 123] Re: =?iso-2022-jp?b?GyRCJWEhPCVrJV4lcxsoQg==?=
    ...
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'].encode())
    [XTest 456] Re: =?iso-2022-jp?b?GyRCJWEhPCVrJV4lcxsoQg==?=
    >>> print(msg['subject'])
    [XTest 456] Re: メールマン

As before, old style subject prefixes are re-ordered.

    >>> msg = message_from_string("""\
    ... Subject: Re: [XTest 123] =?iso-2022-jp?b?GyRCJWEhPCVrJV4lcxsoQg==?=
    ...
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'].encode())
    [XTest 456] Re:
      =?iso-2022-jp?b?GyRCJWEhPCVrJV4lcxsoQg==?=
    >>> print(msg['subject'])
    [XTest 456]  Re: メールマン


In this test case, we get an extra space between the prefix and the original
subject.  It's because the original is *crooked*.  Note that a ``Subject``
starting with '\n ' is generated by some version of Eudora Japanese edition.

    >>> mlist.subject_prefix = '[XTest] '
    >>> msg = message_from_string("""\
    ... Subject:
    ...  Important message
    ...
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'])
    [XTest]  Important message

And again, with an RFC 2047 encoded header.

    >>> msg = message_from_string("""\
    ... Subject:
    ...  =?iso-2022-jp?b?GyRCJWEhPCVrJV4lcxsoQg==?=
    ...
    ... """)
    >>> process(mlist, msg, {})
    >>> print(msg['subject'].encode())
    [XTest] =?iso-2022-jp?b?GyRCJWEhPCVrJV4lcxsoQg==?=
    >>> print(msg['subject'])
    [XTest]  メールマン
