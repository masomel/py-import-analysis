================
Managing members
================

The ``mailman members`` command allows a site administrator to display, add,
and remove members from a mailing list.
::

    >>> ant = create_list('ant@example.com')

    >>> class FakeArgs:
    ...     input_filename = None
    ...     output_filename = None
    ...     list = []
    ...     regular = False
    ...     digest = None
    ...     nomail = None
    ...     role = None
    >>> args = FakeArgs()

    >>> from mailman.commands.cli_members import Members
    >>> command = Members()


Listing members
===============

You can list all the members of a mailing list by calling the command with no
options.  To start with, there are no members of the mailing list.

    >>> args.list = ['ant.example.com']
    >>> command.process(args)
    ant.example.com has no members

Once the mailing list add some members, they will be displayed.

    >>> from mailman.testing.helpers import subscribe
    >>> subscribe(ant, 'Anne', email='anne@example.com')
    <Member: Anne Person <anne@example.com> on ant@example.com
             as MemberRole.member>
    >>> subscribe(ant, 'Bart', email='bart@example.com')
    <Member: Bart Person <bart@example.com> on ant@example.com
             as MemberRole.member>
    >>> command.process(args)
    Anne Person <anne@example.com>
    Bart Person <bart@example.com>

Members are displayed in alphabetical order based on their address.
::

    >>> subscribe(ant, 'Anne', email='anne@aaaxample.com')
    <Member: Anne Person <anne@aaaxample.com> on ant@example.com
             as MemberRole.member>
    >>> command.process(args)
    Anne Person <anne@aaaxample.com>
    Anne Person <anne@example.com>
    Bart Person <bart@example.com>

You can also output this list to a file.

    >>> from tempfile import NamedTemporaryFile
    >>> with NamedTemporaryFile() as outfp:
    ...     args.output_filename = outfp.name
    ...     command.process(args)
    ...     with open(args.output_filename) as infp:
    ...         print(infp.read())
    Anne Person <anne@aaaxample.com>
    Anne Person <anne@example.com>
    Bart Person <bart@example.com>
    >>> args.output_filename = None

The output file can also be standard out.

    >>> args.output_filename = '-'
    >>> command.process(args)
    Anne Person <anne@aaaxample.com>
    Anne Person <anne@example.com>
    Bart Person <bart@example.com>
    >>> args.output_filename = None


Filtering on delivery mode
--------------------------

You can limit output to just the regular non-digest members...

    >>> from mailman.interfaces.member import DeliveryMode
    >>> args.regular = True
    >>> member = ant.members.get_member('anne@example.com')
    >>> member.preferences.delivery_mode = DeliveryMode.plaintext_digests
    >>> command.process(args)
    Anne Person <anne@aaaxample.com>
    Bart Person <bart@example.com>

...or just the digest members.  Furthermore, you can either display all digest
members...

    >>> member = ant.members.get_member('anne@aaaxample.com')
    >>> member.preferences.delivery_mode = DeliveryMode.mime_digests
    >>> args.regular = False
    >>> args.digest = 'any'
    >>> command.process(args)
    Anne Person <anne@aaaxample.com>
    Anne Person <anne@example.com>

...just plain text digest members...

    >>> args.digest = 'plaintext'
    >>> command.process(args)
    Anne Person <anne@example.com>

...just MIME digest members.
::

    >>> args.digest = 'mime'
    >>> command.process(args)
    Anne Person <anne@aaaxample.com>

    # Reset for following tests.
    >>> args.digest = None


Filtering on delivery status
----------------------------

You can also filter the display on the member's delivery status.  By default,
all members are displayed, but you can filter out only those whose delivery
status is enabled...
::

    >>> from mailman.interfaces.member import DeliveryStatus

    >>> member = ant.members.get_member('anne@aaaxample.com')
    >>> member.preferences.delivery_status = DeliveryStatus.by_moderator
    >>> member = ant.members.get_member('bart@example.com')
    >>> member.preferences.delivery_status = DeliveryStatus.by_user

    >>> member = subscribe(ant, 'Cris', email='cris@example.com')
    >>> member.preferences.delivery_status = DeliveryStatus.unknown
    >>> member = subscribe(ant, 'Dave', email='dave@example.com')
    >>> member.preferences.delivery_status = DeliveryStatus.enabled
    >>> member = subscribe(ant, 'Elle', email='elle@example.com')
    >>> member.preferences.delivery_status = DeliveryStatus.by_bounces

    >>> args.nomail = 'enabled'
    >>> command.process(args)
    Anne Person <anne@example.com>
    Dave Person <dave@example.com>

...or disabled by the user...

    >>> args.nomail = 'byuser'
    >>> command.process(args)
    Bart Person <bart@example.com>

...or disabled by the list administrator (or moderator)...

    >>> args.nomail = 'byadmin'
    >>> command.process(args)
    Anne Person <anne@aaaxample.com>

...or by the bounce processor...

    >>> args.nomail = 'bybounces'
    >>> command.process(args)
    Elle Person <elle@example.com>

...or for unknown (legacy) reasons.

    >>> args.nomail = 'unknown'
    >>> command.process(args)
    Cris Person <cris@example.com>

You can also display all members who have delivery disabled for any reason.
::

    >>> args.nomail = 'any'
    >>> command.process(args)
    Anne Person <anne@aaaxample.com>
    Bart Person <bart@example.com>
    Cris Person <cris@example.com>
    Elle Person <elle@example.com>

    # Reset for following tests.
    >>> args.nomail = None


Adding members
==============

You can add members to a mailing list from the command line.  To do so, you
need a file containing email addresses and full names that can be parsed by
``email.utils.parseaddr()``.
::

    >>> bee = create_list('bee@example.com')
    >>> with NamedTemporaryFile('w', buffering=1, encoding='utf-8') as fp:
    ...     for address in ('aperson@example.com',
    ...                     'Bart Person <bperson@example.com>',
    ...                     'cperson@example.com (Cate Person)',
    ...                     ):
    ...         print(address, file=fp)
    ...     fp.flush()
    ...     args.input_filename = fp.name
    ...     args.list = ['bee.example.com']
    ...     command.process(args)

    >>> from operator import attrgetter
    >>> dump_list(bee.members.addresses, key=attrgetter('email'))
    aperson@example.com
    Bart Person <bperson@example.com>
    Cate Person <cperson@example.com>

You can also specify ``-`` as the filename, in which case the addresses are
taken from standard input.
::

    >>> from io import StringIO
    >>> fp = StringIO()
    >>> for address in ('dperson@example.com',
    ...                 'Elly Person <eperson@example.com>',
    ...                 'fperson@example.com (Fred Person)',
    ...                 ):
    ...         print(address, file=fp)
    >>> args.input_filename = '-'
    >>> filepos = fp.seek(0)
    >>> import sys
    >>> try:
    ...     stdin = sys.stdin
    ...     sys.stdin = fp
    ...     command.process(args)
    ... finally:
    ...     sys.stdin = stdin

    >>> dump_list(bee.members.addresses, key=attrgetter('email'))
    aperson@example.com
    Bart Person <bperson@example.com>
    Cate Person <cperson@example.com>
    dperson@example.com
    Elly Person <eperson@example.com>
    Fred Person <fperson@example.com>

Blank lines and lines that begin with '#' are ignored.
::

    >>> with NamedTemporaryFile('w', buffering=1, encoding='utf-8') as fp:
    ...     for address in ('gperson@example.com',
    ...                     '# hperson@example.com',
    ...                     '   ',
    ...                     '',
    ...                     'iperson@example.com',
    ...                     ):
    ...         print(address, file=fp)
    ...     args.input_filename = fp.name
    ...     command.process(args)

    >>> dump_list(bee.members.addresses, key=attrgetter('email'))
    aperson@example.com
    Bart Person <bperson@example.com>
    Cate Person <cperson@example.com>
    dperson@example.com
    Elly Person <eperson@example.com>
    Fred Person <fperson@example.com>
    gperson@example.com
    iperson@example.com

Addresses which are already subscribed are ignored, although a warning is
printed.
::

    >>> with NamedTemporaryFile('w', buffering=1, encoding='utf-8') as fp:
    ...     for address in ('gperson@example.com',
    ...                     'aperson@example.com',
    ...                     'jperson@example.com',
    ...                     ):
    ...         print(address, file=fp)
    ...     args.input_filename = fp.name
    ...     command.process(args)
    Already subscribed (skipping): gperson@example.com
    Already subscribed (skipping): aperson@example.com

    >>> dump_list(bee.members.addresses, key=attrgetter('email'))
    aperson@example.com
    Bart Person <bperson@example.com>
    Cate Person <cperson@example.com>
    dperson@example.com
    Elly Person <eperson@example.com>
    Fred Person <fperson@example.com>
    gperson@example.com
    iperson@example.com
    jperson@example.com


Displaying members
==================

With no arguments, the command displays all members of the list.

    >>> args.input_filename = None
    >>> command.process(args)
    aperson@example.com
    Bart Person <bperson@example.com>
    Cate Person <cperson@example.com>
    dperson@example.com
    Elly Person <eperson@example.com>
    Fred Person <fperson@example.com>
    gperson@example.com
    iperson@example.com
    jperson@example.com
