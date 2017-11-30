================
DMARC mitigation
================

This rule only matches in order to jump to the moderation chain to reject or
discard the message.  The rule looks at the list's ``dmarc_mitigate_action``
and if it is other than ``no_mitigation``, it checks the domain of the
``From:`` address for a DMARC policy.  Depending on various settings, reject
or discard the message, or just flag it for the dmarc handler to apply DMARC
mitigations to the message.

    >>> mlist = create_list('ant@example.com')
    >>> rule = config.rules['dmarc-mitigation']
    >>> print(rule.name)
    dmarc-mitigation

First we set up a mock to return predictable responses to DNS lookups.  This
returns ``p=reject`` for the ``example.biz`` domain and not for any others.

    >>> from mailman.rules.tests.test_dmarc import get_dns_resolver
    >>> ignore = cleanups.enter_context(get_dns_resolver())

Use test data for the organizational domain suffixes.

    >>> from mailman.rules.tests.test_dmarc import use_test_organizational_data
    >>> cleanups.enter_context(use_test_organizational_data())

A message ``From:`` a domain without a DMARC policy does not set any flags.

    >>> from mailman.interfaces.mailinglist import DMARCMitigateAction
    >>> mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
    >>> msg = message_from_string("""\
    ... From: aperson@example.org
    ... To: ant@example.com
    ... Subject: A posted message
    ...
    ... """)
    >>> msgdata = {}
    >>> rule.check(mlist, msg, msgdata)
    False
    >>> msgdata
    {}

Even if the ``From:`` domain publishes ``p=reject``, no flags are set if the
list's action is ``no_mitigation``.

    >>> mlist.dmarc_mitigate_action = DMARCMitigateAction.no_mitigation
    >>> msg = message_from_string("""\
    ... From: aperson@example.biz
    ... To: ant@example.com
    ... Subject: A posted message
    ...
    ... """)
    >>> msgdata = {}
    >>> rule.check(mlist, msg, msgdata)
    False
    >>> msgdata
    {}

With a mitigation strategy chosen, the message is flagged.

    >>> mlist.dmarc_mitigate_action = DMARCMitigateAction.munge_from
    >>> msg = message_from_string("""\
    ... From: aperson@example.biz
    ... To: ant@example.com
    ... Subject: A posted message
    ...
    ... """)
    >>> msgdata = {}
    >>> rule.check(mlist, msg, msgdata)
    False
    >>> msgdata
    {'dmarc': True}

Subdomains which don't have a policy will check the organizational domain.

    >>> msg = message_from_string("""\
    ... From: aperson@sub.domain.example.biz
    ... To: ant@example.com
    ... Subject: A posted message
    ...
    ... """)
    >>> msgdata = {}
    >>> rule.check(mlist, msg, msgdata)
    False
    >>> msgdata
    {'dmarc': True}

The list's action can also be set to immediately discard or reject the
message.

    >>> mlist.dmarc_mitigate_action = DMARCMitigateAction.discard
    >>> msg = message_from_string("""\
    ... From: aperson@example.biz
    ... To: ant@example.com
    ... Subject: A posted message
    ... Message-ID: <xxx_message_id@example.biz>
    ...
    ... """)
    >>> msgdata = {}
    >>> rule.check(mlist, msg, msgdata)
    True
    >>> dump_msgdata(msgdata)
    dmarc             : True
    moderation_action : discard
    moderation_reasons: ['DMARC moderation']
    moderation_sender : aperson@example.biz

We can reject the message with a default reason.

    >>> mlist.dmarc_mitigate_action = DMARCMitigateAction.reject
    >>> msg = message_from_string("""\
    ... From: aperson@example.biz
    ... To: ant@example.com
    ... Subject: A posted message
    ... Message-ID: <xxx_message_id@example.biz>
    ...
    ... """)
    >>> msgdata = {}
    >>> rule.check(mlist, msg, msgdata)
    True
    >>> dump_msgdata(msgdata)
    dmarc             : True
    moderation_action : reject
    moderation_reasons: ['You are not allowed to post to this mailing list...
    moderation_sender : aperson@example.biz

And, we can reject with a custom message.

    >>> mlist.dmarc_moderation_notice = 'A silly reason'
    >>> msg = message_from_string("""\
    ... From: aperson@example.biz
    ... To: ant@example.com
    ... Subject: A posted message
    ... Message-ID: <xxx_message_id@example.biz>
    ...
    ... """)
    >>> msgdata = {}
    >>> rule.check(mlist, msg, msgdata)
    True
    >>> dump_msgdata(msgdata)
    dmarc             : True
    moderation_action : reject
    moderation_reasons: ['A silly reason']
    moderation_sender : aperson@example.biz
