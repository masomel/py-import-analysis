=======================
Banning email addresses
=======================

Email addresses can be banned from ever subscribing, either to a specific
mailing list or globally within the Mailman system.  Both explicit email
addresses and email address patterns can be banned.

Bans are managed through the `Ban Manager`.  There are ban managers for
specific lists, and there is a global ban manager.  To get access to the
global ban manager, adapt ``None``.

    >>> from mailman.interfaces.bans import IBanManager
    >>> global_bans = IBanManager(None)

At first, no email addresses are banned globally.

    >>> global_bans.is_banned('anne@example.com')
    False

To get a list-specific ban manager, adapt the mailing list object.

    >>> mlist = create_list('test@example.com')
    >>> test_bans = IBanManager(mlist)

There are no bans for this particular list.

    >>> test_bans.is_banned('bart@example.com')
    False


Specific bans
=============

An email address can be banned from a specific mailing list by adding a ban to
the list's ban manager.

    >>> test_bans.ban('cris@example.com')
    >>> test_bans.is_banned('cris@example.com')
    True
    >>> test_bans.is_banned('bart@example.com')
    False

However, this is not a global ban.

    >>> global_bans.is_banned('cris@example.com')
    False


Global bans
===========

An email address can be banned globally, so that it cannot be subscribed to
any mailing list.

    >>> global_bans.ban('dave@example.com')

Because there is a global ban, Dave is also banned from the mailing list.

    >>> test_bans.is_banned('dave@example.com')
    True

Even when a new mailing list is created, Dave is still banned from this list
because of his global ban.

    >>> sample = create_list('sample@example.com')
    >>> sample_bans = IBanManager(sample)
    >>> sample_bans.is_banned('dave@example.com')
    True

Dave is of course banned globally.

    >>> global_bans.is_banned('dave@example.com')
    True

Cris however is not banned globally.

    >>> global_bans.is_banned('cris@example.com')
    False

Even though Cris is not banned globally, we can add a global ban for her.

    >>> global_bans.ban('cris@example.com')
    >>> global_bans.is_banned('cris@example.com')
    True

Cris is now banned from all mailing lists.

    >>> test_bans.is_banned('cris@example.com')
    True
    >>> sample_bans.is_banned('cris@example.com')
    True

We can remove the global ban to once again just ban her address from just the
test list.

    >>> global_bans.unban('cris@example.com')
    >>> global_bans.is_banned('cris@example.com')
    False
    >>> test_bans.is_banned('cris@example.com')
    True
    >>> sample_bans.is_banned('cris@example.com')
    False


Regular expression bans
=======================

Entire email address patterns can be banned, both for a specific mailing list
and globally, just as specific addresses can be banned.  Use this for example,
when an entire domain is a spam faucet.  When using a pattern, the email
address must start with a caret (^).

    >>> test_bans.ban('^.*@example.org')

Now, no one from example.org can subscribe to the test mailing list.

    >>> test_bans.is_banned('elle@example.org')
    True
    >>> test_bans.is_banned('eperson@example.org')
    True

example.com addresses are not banned.

    >>> test_bans.is_banned('elle@example.com')
    False

example.org addresses are not banned globally, nor for any other mailing
list.

    >>> sample_bans.is_banned('elle@example.org')
    False
    >>> global_bans.is_banned('elle@example.org')
    False

Of course, we can ban everyone from example.org globally too.

    >>> global_bans.ban('^.*@example.org')
    >>> sample_bans.is_banned('elle@example.org')
    True
    >>> global_bans.is_banned('elle@example.org')
    True

We can remove the mailing list ban on the pattern, though the global ban will
still be in place.

    >>> test_bans.unban('^.*@example.org')
    >>> test_bans.is_banned('elle@example.org')
    True
    >>> sample_bans.is_banned('elle@example.org')
    True
    >>> global_bans.is_banned('elle@example.org')
    True

But once the global ban is removed, everyone from example.org can subscribe to
the mailing lists.

    >>> global_bans.unban('^.*@example.org')
    >>> test_bans.is_banned('elle@example.org')
    False
    >>> sample_bans.is_banned('elle@example.org')
    False
    >>> global_bans.is_banned('elle@example.org')
    False


Adding and removing bans
========================

It is not an error to add a ban more than once.  These are just ignored.

    >>> test_bans.ban('fred@example.com')
    >>> test_bans.ban('fred@example.com')
    >>> test_bans.is_banned('fred@example.com')
    True

Nor is it an error to remove a ban more than once.

    >>> test_bans.unban('fred@example.com')
    >>> test_bans.unban('fred@example.com')
    >>> test_bans.is_banned('fred@example.com')
    False
