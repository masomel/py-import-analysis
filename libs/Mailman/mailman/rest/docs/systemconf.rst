====================
System configuration
====================

The entire system configuration is available through the REST API.  You can
get a list of all defined sections.

    >>> dump_json('http://localhost:9001/3.0/system/configuration')
    http_etag: ...
    sections: ['antispam', 'archiver.mail_archive', 'archiver.master', ...
    self_link: http://localhost:9001/3.0/system/configuration

You can also get all the values for a particular section, such as the
``[mailman]`` section...

    >>> dump_json('http://localhost:9001/3.0/system/configuration/mailman')
    cache_life: 7d
    default_language: en
    email_commands_max_lines: 10
    filtered_messages_are_preservable: no
    html_to_plain_text_command: /usr/bin/lynx -dump $filename
    http_etag: ...
    layout: testing
    listname_chars: [-_.0-9a-z]
    noreply_address: noreply
    pending_request_life: 3d
    post_hook:
    pre_hook:
    self_link: http://localhost:9001/3.0/system/configuration/mailman
    sender_headers: from from_ reply-to sender
    site_owner: noreply@example.com

...or the ``[dmarc]`` section (or any other).

    >>> dump_json('http://localhost:9001/3.0/system/configuration/dmarc')
    cache_lifetime: 7d
    http_etag: ...
    org_domain_data_url: https://publicsuffix.org/list/public_suffix_list.dat
    resolver_lifetime: 5s
    resolver_timeout: 3s
    self_link: http://localhost:9001/3.0/system/configuration/dmarc

Dotted section names work too, for example, to get the French language
settings section.

    >>> dump_json('http://localhost:9001/3.0/system/configuration/language.fr')
    charset: iso-8859-1
    description: French
    enabled: yes
    http_etag: ...
    self_link: http://localhost:9001/3.0/system/configuration/language.fr
