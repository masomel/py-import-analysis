==========================
Mailing list configuration
==========================

Mailing lists can be configured via the REST API.

    >>> mlist = create_list('ant@example.com')
    >>> transaction.commit()


Reading a configuration
=======================

All readable attributes for a list are available on a sub-resource.

    >>> dump_json('http://localhost:9001/3.0/lists/ant@example.com/config')
    acceptable_aliases: []
    admin_immed_notify: True
    admin_notify_mchanges: False
    administrivia: True
    advertised: True
    allow_list_posts: True
    anonymous_list: False
    archive_policy: public
    autorespond_owner: none
    autorespond_postings: none
    autorespond_requests: none
    autoresponse_grace_period: 90d
    autoresponse_owner_text:
    autoresponse_postings_text:
    autoresponse_request_text:
    bounces_address: ant-bounces@example.com
    collapse_alternatives: True
    convert_html_to_plaintext: False
    created_at: 20...T...
    default_member_action: defer
    default_nonmember_action: hold
    description:
    digest_footer_uri:
    digest_header_uri:
    digest_last_sent_at: None
    digest_send_periodic: True
    digest_size_threshold: 30.0
    digest_volume_frequency: monthly
    digests_enabled: True
    display_name: Ant
    dmarc_mitigate_action: no_mitigation
    dmarc_mitigate_unconditionally: False
    dmarc_moderation_notice:
    dmarc_wrapped_message_text:
    filter_content: False
    first_strip_reply_to: False
    footer_uri:
    fqdn_listname: ant@example.com
    goodbye_message_uri:
    header_uri:
    http_etag: "..."
    include_rfc2369_headers: True
    info:
    join_address: ant-join@example.com
    last_post_at: None
    leave_address: ant-leave@example.com
    list_name: ant
    mail_host: example.com
    moderator_password: None
    next_digest_number: 1
    no_reply_address: noreply@example.com
    owner_address: ant-owner@example.com
    post_id: 1
    posting_address: ant@example.com
    posting_pipeline: default-posting-pipeline
    reply_goes_to_list: no_munging
    reply_to_address:
    request_address: ant-request@example.com
    send_welcome_message: True
    subject_prefix: [Ant]
    subscription_policy: confirm
    volume: 1
    welcome_message_uri:


Changing the full configuration
===============================

Not all of the readable attributes can be set through the web interface.  The
ones that can, can either be set via ``PUT`` or ``PATCH``.  ``PUT`` changes
all the writable attributes in one request.

When using ``PUT``, all writable attributes must be included.

    >>> dump_json('http://localhost:9001/3.0/lists/'
    ...           'ant@example.com/config',
    ...           dict(
    ...             acceptable_aliases=['one@example.com', 'two@example.com'],
    ...             admin_immed_notify=False,
    ...             admin_notify_mchanges=True,
    ...             administrivia=False,
    ...             advertised=False,
    ...             anonymous_list=True,
    ...             archive_policy='never',
    ...             autorespond_owner='respond_and_discard',
    ...             autorespond_postings='respond_and_continue',
    ...             autorespond_requests='respond_and_discard',
    ...             autoresponse_grace_period='45d',
    ...             autoresponse_owner_text='the owner',
    ...             autoresponse_postings_text='the mailing list',
    ...             autoresponse_request_text='the robot',
    ...             display_name='Fnords',
    ...             description='This is my mailing list',
    ...             include_rfc2369_headers=False,
    ...             info='This is the mailing list information',
    ...             allow_list_posts=False,
    ...             digest_send_periodic=False,
    ...             digest_size_threshold=10.5,
    ...             digest_volume_frequency='yearly',
    ...             digests_enabled=False,
    ...             dmarc_mitigate_action='munge_from',
    ...             dmarc_mitigate_unconditionally=False,
    ...             dmarc_moderation_notice='Some moderation notice',
    ...             dmarc_wrapped_message_text='some message text',
    ...             posting_pipeline='virgin',
    ...             filter_content=True,
    ...             first_strip_reply_to=True,
    ...             convert_html_to_plaintext=True,
    ...             collapse_alternatives=False,
    ...             reply_goes_to_list='point_to_list',
    ...             reply_to_address='bee@example.com',
    ...             send_welcome_message=False,
    ...             subject_prefix='[ant]',
    ...             subscription_policy='moderate',
    ...             default_member_action='hold',
    ...             default_nonmember_action='discard',
    ...             moderator_password='password',
    ...             ),
    ...           'PUT')
    content-length: 0
    date: ...
    server: WSGIServer/...
    status: 204

These values are changed permanently.

    >>> dump_json('http://localhost:9001/3.0/lists/'
    ...           'ant@example.com/config')
    acceptable_aliases: ['one@example.com', 'two@example.com']
    admin_immed_notify: False
    admin_notify_mchanges: True
    administrivia: False
    advertised: False
    allow_list_posts: False
    anonymous_list: True
    archive_policy: never
    autorespond_owner: respond_and_discard
    autorespond_postings: respond_and_continue
    autorespond_requests: respond_and_discard
    autoresponse_grace_period: 45d
    autoresponse_owner_text: the owner
    autoresponse_postings_text: the mailing list
    autoresponse_request_text: the robot
    ...
    collapse_alternatives: False
    convert_html_to_plaintext: True
    ...
    default_member_action: hold
    default_nonmember_action: discard
    description: This is my mailing list
    ...
    digest_send_periodic: False
    digest_size_threshold: 10.5
    digest_volume_frequency: yearly
    digests_enabled: False
    display_name: Fnords
    dmarc_mitigate_action: munge_from
    dmarc_mitigate_unconditionally: False
    dmarc_moderation_notice: Some moderation notice
    dmarc_wrapped_message_text: some message text
    filter_content: True
    first_strip_reply_to: True
    footer_uri:
    fqdn_listname: ant@example.com
    ...
    include_rfc2369_headers: False
    ...
    moderator_password: {plaintext}password
    ...
    posting_pipeline: virgin
    reply_goes_to_list: point_to_list
    reply_to_address: bee@example.com
    ...
    send_welcome_message: False
    subject_prefix: [ant]
    subscription_policy: moderate
    ...


Changing a partial configuration
================================

Using ``PATCH``, you can change just one attribute.

    >>> dump_json('http://localhost:9001/3.0/lists/'
    ...           'ant@example.com/config',
    ...           dict(display_name='My List'),
    ...           'PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

These values are changed permanently.

    >>> print(mlist.display_name)
    My List


Sub-resources
=============

Mailing list configuration variables are actually available as sub-resources
on the mailing list.  Their values can be retrieved and set through the
sub-resource.


Simple resources
----------------

You can view the current value of the sub-resource.

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/config/display_name')
    display_name: My List
    http_etag: ...

The resource can be changed by PUTting to it.  Note that the value still
requires a dictionary, and that dictionary must have a single key matching the
name of the resource.
::

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/config/display_name',
    ...           dict(display_name='Your List'),
    ...           'PUT')
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/config/display_name')
    display_name: Your List
    http_etag: ...

PATCH works the same way, with the same effect, so you can choose to use
either method.

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/config/display_name',
    ...           dict(display_name='Their List'),
    ...           'PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/config/display_name')
    display_name: Their List
    http_etag: ...


Acceptable aliases
------------------

These are recipient aliases that can be used in the ``To:`` and ``CC:``
headers instead of the posting address.  They are often used in forwarded
emails.  By default, a mailing list has no acceptable aliases.

    >>> from mailman.interfaces.mailinglist import IAcceptableAliasSet
    >>> IAcceptableAliasSet(mlist).clear()
    >>> transaction.commit()
    >>> dump_json('http://localhost:9001/3.0/lists/'
    ...           'ant@example.com/config/acceptable_aliases')
    acceptable_aliases: []
    http_etag: "..."

We can add a few by ``PUT``-ing them on the sub-resource.  The keys in the
dictionary are ignored.

    >>> dump_json('http://localhost:9001/3.0/lists/'
    ...           'ant@example.com/config/acceptable_aliases',
    ...           dict(acceptable_aliases=['foo@example.com',
    ...                                    'bar@example.net']),
    ...           'PUT')
    content-length: 0
    date: ...
    server: WSGIServer/...
    status: 204

Aliases are returned as a list on the ``aliases`` key.

    >>> response = call_http(
    ...     'http://localhost:9001/3.0/lists/'
    ...     'ant@example.com/config/acceptable_aliases')
    >>> for alias in response['acceptable_aliases']:
    ...     print(alias)
    bar@example.net
    foo@example.com

The mailing list has its aliases set.

    >>> from mailman.interfaces.mailinglist import IAcceptableAliasSet
    >>> aliases = IAcceptableAliasSet(mlist)
    >>> for alias in sorted(aliases.aliases):
    ...     print(alias)
    bar@example.net
    foo@example.com


Header matches
--------------

Mailman can do pattern based header matching during its normal rule
processing.  Each mailing list can also be configured with a set of header
matching regular expression rules.  These can be used to impose list-specific
header filtering with the same semantics as the global ``[antispam]`` section,
or to have a different action.

The list of header matches for a mailing list are returned on the
``header-matches`` child of this list.

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches')
    http_etag: "..."
    start: 0
    total_size: 0

New header matches can be created by POSTing to the resource.
::

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches', {
    ...           'header': 'X-Spam-Flag',
    ...           'pattern': '^Yes',
    ...           })
    content-length: 0
    ...
    location: .../3.0/lists/ant.example.com/header-matches/0
    ...
    status: 201

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches/0')
    header: x-spam-flag
    http_etag: "..."
    pattern: ^Yes
    position: 0
    self_link: http://localhost:9001/3.0/lists/ant.example.com/header-matches/0

To follow the global antispam action, the header match rule must not specify
an ``action`` key, which names the chain to jump to if the rule matches.  If
the default antispam action is changed in the configuration file and Mailman
is restarted, those rules will get the new jump action.  If a specific action
is desired, the ``action`` key must name a valid chain to jump to.
::

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches', {
    ...           'header': 'X-Spam-Status',
    ...           'pattern': '^Yes',
    ...           'action': 'discard',
    ...           })
    content-length: 0
    ...
    location: .../3.0/lists/ant.example.com/header-matches/1
    ...
    status: 201

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches/1')
    action: discard
    header: x-spam-status
    http_etag: "..."
    pattern: ^Yes
    position: 1
    self_link: http://localhost:9001/3.0/lists/ant.example.com/header-matches/1

The resource can be changed by PATCHing it.  The ``position`` key can be used
to change the priority of the header match in the list.  If it is not supplied,
the priority is not changed.
::

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches/1',
    ...           dict(pattern='^No', action='accept'),
    ...           'PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204
    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches/1')
    action: accept
    header: x-spam-status
    http_etag: "..."
    pattern: ^No
    position: 1
    self_link: http://localhost:9001/3.0/lists/ant.example.com/header-matches/1

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches/1',
    ...           dict(position=0),
    ...           'PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204
    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches')
    entry 0:
        action: accept
        header: x-spam-status
        http_etag: "..."
        pattern: ^No
        position: 0
        self_link: .../lists/ant.example.com/header-matches/0
    entry 1:
        header: x-spam-flag
        http_etag: "..."
        pattern: ^Yes
        position: 1
        self_link: .../lists/ant.example.com/header-matches/1
    http_etag: "..."
    start: 0
    total_size: 2

The PUT method can replace an entire header match.  The ``position`` key is
optional; if it is omitted, the order will not be changed.
::

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches/1',
    ...           dict(header='X-Spam-Status',
    ...                pattern='^Yes',
    ...                action='hold',
    ...           ), 'PUT')
    content-length: 0
    date: ...
    server: ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches/1')
    action: hold
    header: x-spam-status
    http_etag: "..."
    pattern: ^Yes
    position: 1
    self_link: http://localhost:9001/3.0/lists/ant.example.com/header-matches/1

A header match can be removed using the DELETE method.
::

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches/1',
    ...           method='DELETE')
    content-length: 0
    ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches')
    entry 0:
        action: accept
        header: x-spam-status
        http_etag: "..."
        pattern: ^No
        position: 0
        self_link: .../lists/ant.example.com/header-matches/0
    http_etag: "..."
    start: 0
    total_size: 1

The mailing list's header matches can be cleared by issuing a DELETE request on
the top resource.
::

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches',
    ...           method='DELETE')
    content-length: 0
    ...
    status: 204

    >>> dump_json('http://localhost:9001/3.0/lists/ant.example.com'
    ...           '/header-matches')
    http_etag: "..."
    start: 0
    total_size: 0
