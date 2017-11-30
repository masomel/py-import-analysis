=============================
 Hooking up your mail server
=============================

Mailman needs to communicate with your *MTA* (*mail transport agent*
or *mail server*, the software which handles sending mail across the
Internet), both to accept incoming mail and to deliver outgoing mail.
Mailman itself never delivers messages to the end user.  It sends them
to its immediate upstream MTA, which delivers them.  In the same way,
Mailman never receives mail directly.  Mail from outside always comes
via the MTA.

Mailman accepts incoming messages from the MTA using the `Local Mail Transfer
Protocol`_ (LMTP_) interface.  LMTP is much more efficient than spawning a
process just to do the delivery.  Most open source MTAs support LMTP for local
delivery.  If yours doesn't, and you need to use a different interface, please
ask on the `mailing list or on IRC`_.

Mailman passes all outgoing messages to the MTA using the `Simple Mail
Transfer Protocol`_ (SMTP_).

Cooperation between Mailman and the MTA requires some configuration of
both.  MTA configuration differs for each of the available MTAs, and
there is a section for each one.  Instructions for Postfix and Exim (v4)
are given below.  We would really appreciate a contribution of a
configuration for Sendmail, and welcome information about other popular
open source mail servers.

Configuring Mailman to communicate with the MTA is straightforward, and
basically the same for all MTAs.  Here are the default settings; if you need
to change them, edit your ``mailman.cfg`` file::

    [mta]
    incoming: mailman.mta.postfix.LMTP
    outgoing: mailman.mta.deliver.deliver
    lmtp_host: 127.0.0.1
    lmtp_port: 8024
    smtp_host: localhost
    smtp_port: 25
    configuration: python:mailman.config.postfix

This configuration is for a system where Mailman and the MTA are on
the same host.

Note that the modules that configure the communication protocol (especially
``incoming``) are full-fledged Python modules, and may use these configuration
parameters to automatically configure the MTA to recognize the list addresses
and other attributes of the communication channel.  This is why some
constraints on the format of attributes arise (e.g., ``lmtp_host``), even
though Mailman itself has no problem with them.

It is possible (although not documented here) to completely replace or
override the default mechanisms to handle both incoming and outgoing mail.
Mailman is highly customizable here!

The ``incoming`` and ``outgoing`` parameters identify the Python objects used
to communicate with the MTA.  The ``python:`` scheme indicates that the paths
should be a dotted Python module specification.  The ``deliver`` module used
in ``outgoing`` should be satisfactory for most MTAs.  The ``postfix`` module
in ``incoming`` is specific to the Postfix MTA.  See the section for your MTA
below for details on these parameters.

``lmtp_host`` and ``lmtp_port`` are parameters which are used by Mailman, but
also will be passed to the MTA to identify the Mailman host.  The "same host"
case is special; some MTAs (including Postfix) do not recognize "localhost",
and need the numerical IP address.  If they are on different hosts,
``lmtp_host`` should be set to the domain name or IP address of the Mailman
host.  ``lmtp_port`` is fairly arbitrary (there is no standard port for LMTP).
Use any port convenient for your site.  "8024" is as good as any, unless
another service is using it.

``smtp_host`` and ``smtp_port`` are parameters used to identify the MTA to
Mailman.  If the MTA and Mailman are on separate hosts, ``smtp_host`` should
be set to the domain name or IP address of the MTA host.  ``smtp_port`` will
almost always be 25, which is the standard port for SMTP.  (Some special site
configurations set it to a different port.  If you need this, you probably
already know that, know why, and what to do, too!)

Mailman also provides many other configuration variables that you can
use to tweak performance for your operating environment.  See the
``src/mailman/config/schema.cfg`` file for details.


Postfix
=======

Postfix_ is an open source mail server by Wietse Venema.


Mailman settings
----------------

You need to tell Mailman that you are using the Postfix mail server.  In your
``mailman.cfg`` file, add the following section::

    [mta]
    incoming: mailman.mta.postfix.LMTP
    outgoing: mailman.mta.deliver.deliver
    lmtp_host: mail.example.com
    lmtp_port: 8024
    smtp_host: mail.example.com
    smtp_port: 25

Some of these settings are already the default, so take a look at Mailman's
``src/mailman/config/schema.cfg`` file for details.  You'll need to change the
``lmtp_host`` and ``smtp_host`` to the appropriate host names of course.
Generally, Postfix will listen for incoming SMTP connections on port 25.
Postfix will deliver via LMTP over port 24 by default, however if you are not
running Mailman as root, you'll need to change this to a higher port number,
as shown above.


Basic Postfix connections
-------------------------

There are several ways to hook Postfix up to Mailman, so here are the simplest
instructions.  The following settings should be added to Postfix's ``main.cf``
file.

Mailman supports a technique called `Variable Envelope Return Path`_ (VERP) to
disambiguate and accurately record bounces.  By default Mailman's VERP
delimiter is the `+` sign, so adding this setting allows Postfix to properly
handle Mailman's VERP'd messages::

    # Support the default VERP delimiter.
    recipient_delimiter = +

In older versions of Postfix, unknown local recipients generated a temporary
failure.  It's much better (and the default in newer Postfix releases) to
treat them as permanent failures.  You can add this to your ``main.cf`` file
if needed (use the `postconf`_ command to check the defaults)::

    unknown_local_recipient_reject_code = 550

While generally not necessary if you set ``recipient_delimiter`` as described
above, it's better for Postfix to not treat ``owner-`` and ``-request``
addresses specially::

    owner_request_special = no


Transport maps
--------------

By default, Mailman works well with Postfix transport maps as a way to deliver
incoming messages to Mailman's LMTP server.  Mailman will automatically write
the correct transport map when its ``mailman aliases`` command is run, or
whenever a mailing list is created or removed via other commands. Mailman
supports two type of transport map tables for Postfix, namely ``hash`` and
``regexp``. Tables using hash are processed by ``postmap`` command. To use this
format, you should have ``postmap`` command available on the host running
Mailman. It is also the default one of the two. To connect Postfix to
Mailman's LMTP server, add the following to Postfix's ``main.cf`` file::

    transport_maps =
        hash:/path-to-mailman/var/data/postfix_lmtp
    local_recipient_maps =
        hash:/path-to-mailman/var/data/postfix_lmtp
    relay_domains =
        hash:/path-to-mailman/var/data/postfix_domains

where ``path-to-mailman`` is replaced with the actual path that you're running
Mailman from.  Setting ``local_recipient_maps`` as well as ``transport_maps``
allows Postfix to properly reject all messages destined for non-existent local
users.  Setting `relay_domains`_ means Postfix will start to accept mail for
newly added domains even if they are not part of `mydestination`_.

Note that if you are not using virtual domains, then `relay_domains`_ isn't
strictly needed (but it is harmless).  All you need to do in this scenario is
to make sure that Postfix accepts mail for your one domain, normally by
including it in ``mydestination``.

Regular Expression tables remove the additional dependency of having ``postmap``
command available to Mailman. If you want to use ``regexp`` or Regular
Expression tables, then add the following to Postfix's ``main.cf`` file::

    transport_maps =
        regexp:/path-to-mailman/var/data/postfix_lmtp
    local_recipient_maps =
        regexp:/path-to-mailman/var/data/postfix_lmtp
    relay_domains =
        regexp:/path-to-mailman/var/data/postfix_domains

You will also have to instruct Mailman to generate regexp tables instead of hash
tables by adding the following configuration to ``mailman.cfg``::

    [mta]
    incoming: mailman.mta.postfix.LMTP
    outgoing: mailman.mta.deliver.deliver
    lmtp_host: mail.example.com
    lmtp_port: 8024
    smtp_host: mail.example.com
    smtp_port: 25
    configuration: /path/to/postfix-mailman.cfg

Also you will have to create another configuration file called as
``postfix-mailman.cfg`` and add its path to the ``configuration`` parameter
above. The ``postfix-mailman.cfg`` would look like this::

    [postfix]
    transport_file_type: regex


Postfix documentation
---------------------

For more information regarding how to configure Postfix, please see
the Postfix documentation at:

.. _`The official Postfix documentation`:
   http://www.postfix.org/documentation.html
.. _`The reference page for all Postfix configuration parameters`:
   http://www.postfix.org/postconf.5.html
.. _`relay_domains`: http://www.postfix.org/postconf.5.html#relay_domains
.. _`mydestination`: http://www.postfix.org/postconf.5.html#mydestination


Exim
====

`Exim 4`_ is an MTA maintained by the `University of Cambridge`_ and
distributed by most open source OS distributions.

Mailman settings
----------------

Add or edit a stanza like this in mailman.cfg::

    [mta]
    # For all Exim4 installations.
    incoming: mailman.mta.exim4.LMTP
    outgoing: mailman.mta.deliver.deliver
    # Typical single host with MTA and Mailman configuration.
    # Adjust to your system's configuration.
    # Exim happily works with the "localhost" alias rather than IP address.
    lmtp_host: localhost
    smtp_host: localhost
    # Mailman should not be run as root.
    # Use any convenient port > 1024.  8024 is a convention, but can be
    # changed if there is a conflict with other software using that port.
    lmtp_port: 8024
    # smtp_port rarely needs to be set.
    smtp_port: 25
    # Exim4-specific configuration parameter defaults.  Currently empty.
    configuration: python:mailman.config.exim4

For further information about these settings, see
``mailman/config/schema.cfg``.

Exim4 configuration
-------------------

The configuration presented below is mostly boilerplate that allows Exim to
automatically discover your list addresses, and route both posts and
administrative messages to the right Mailman services.  For this reason, the
`mailman.mta.exim4` module ends up with all methods being no-ops.

This configuration is field-tested in a Debian "conf.d"-style Exim
installation, with multiple configuration files that are assembled by a
Debian-specific script.  If your Exim v4 installation is structured
differently, ignore the comments indicating location in the Debian
installation.
::

    # /etc/exim4/conf.d/main/25_mm3_macros
    # The colon-separated list of domains served by Mailman.
    domainlist mm_domains=list.example.net

    MM3_LMTP_PORT=8024

    # MM3_HOME must be set to mailman's var directory, wherever it is
    # according to your installation.
    MM3_HOME=/opt/mailman/var
    MM3_UID=list
    MM3_GID=list

    ################################################################
    # The configuration below is boilerplate:
    # you should not need to change it.

    # The path to the list receipt (used as the required file when
    # matching list addresses)
    MM3_LISTCHK=MM3_HOME/lists/${local_part}.${domain}

    # /etc/exim4/conf.d/router/455_mm3_router
    mailman3_router:
      driver = accept
      domains = +mm_domains
      require_files = MM3_LISTCHK
      local_part_suffix_optional
      local_part_suffix = \
         -bounces   : -bounces+* : \
         -confirm   : -confirm+* : \
         -join      : -leave     : \
         -owner     : -request   : \
         -subscribe : -unsubscribe
      transport = mailman3_transport

    # /etc/exim4/conf.d/transport/55_mm3_transport
    mailman3_transport:
      driver = smtp
      protocol = lmtp
      allow_localhost
      hosts = localhost
      port = MM3_LMTP_PORT
      rcpt_include_affixes = true

Troubleshooting
---------------

The most likely causes of failure to deliver to Mailman are typos in the
configuration, and errors in the ``MM3_HOME`` macro or the ``mm_domains``
list.  Mismatches in the LMTP port could be a cause.  Finally, Exim's router
configuration is order-sensitive.  Especially if you are being tricky and
supporting Mailman 2 and Mailman 3 at the same time, you could have one shadow
the other.

Exim 4 documentation
--------------------

There is `copious documentation for Exim`_.  The parts most relevant to
configuring communication with Mailman 3 are the chapters on the `accept
router`_ and the `LMTP transport`_.  Unless you are already familiar
with Exim configuration, you probably want to start with the chapter on
`how Exim receives and delivers mail`.

.. _`Exim 4`: http://www.exim.org/
.. _`University of Cambridge`: http://www.cam.ac.uk/
.. _`copious documentation for Exim`: http://www.exim.org/docs.html
.. _`accept router`: http://www.exim.org/exim-html-current/doc/html/spec_html/ch-the_accept_router.html
.. _`LMTP transport`: http://www.exim.org/exim-html-current/doc/html/spec_html/ch-the_lmtp_transport.html
.. _`how Exim receives and delivers mail`: http://www.exim.org/exim-html-current/doc/html/spec_html/ch-how_exim_receives_and_delivers_mail.html


qmail
=====

qmail_ is a MTA written by djb_ and, though old and not updated, still
bulletproof and occassionally in use.

Mailman settings
----------------

Mostly defaults in mailman.cfg::

    [mta]
    # NullMTA is just implementing the interface and thus satisfying Mailman
    # without doing anything fancy
    incoming: mailman.mta.null.NullMTA
    # Mailman should not be run as root.
    # Use any convenient port > 1024.  8024 is a convention, but can be
    # changed if there is a conflict with other software using that port.
    lmtp_port: 8024

This will listen on ``localhost:8024`` with LMTP and deliver outgoing messages
to ``localhost:25``.  See ``mailman/config/schema.cfg`` for more information
on these settings.

qmail configuration
-------------------

It is assumed that qmail is configured to use the ``.qmail*`` files in a user’s
home directory, however the instructions should easily be adaptable to other
qmail configurations.  However, it is required that Mailman has a (sub)domain
respectively a namespace on its own.  A helper script called ``qmail-lmtp`` is
needed and can be found in the ``contrib/`` directory of the Mailman source
tree and assumed to be on ``$PATH`` here.

As qmail puts every namespace in the address, we have to filter it out again.
If your main domain is ``example.com`` and you assign ``lists.example.com`` to
the user ``mailman``, qmail will give you the destination address
``mailman-spam@lists.example.com`` while it should actually be
``spam@lists.example.com``.  The second argument to ``qmail-lmtp`` defines
how many parts (separated by dashes) to filter out.  The first argument
specifies the LMTP port of Mailman.  Long story short, as user mailman:
::

    % chmod +t "$HOME"
    % echo '|qmail-lmtp 1 8042' > .qmail # put appropriate values here
    % ln -sf .qmail .qmail-default
    % chmod -t "$HOME"

.. _qmail: https://cr.yp.to/qmail.html
.. _djb: https://cr.yp.to


Sendmail
========

The core Mailman developers generally do not use Sendmail, so experience is
limited.  Any and all contributions are welcome!  The follow information from
a post by Gary Algier <gaa@ulticom.com> may be useful as a starting point,
although it describes Mailman 2:

    I have it working fine.  I recently replaced a very old implementation
    of sendmail and Mailman 2 on Solaris with a new one on CentOS 6.  When I
    did so, I used the POSTFIX_ALIAS_CMD mechanism to automatically process
    the aliases.  See::

        https://mail.python.org/pipermail/mailman-users/2004-June/037518.html

    In mm_cfg.py::

         MTA='Postfix'
         POSTFIX_ALIAS_CMD = '/usr/bin/sudo /etc/mail/import-mailman-aliases'

    /etc/mail/import-mailman-aliases contains::

         #! /bin/sh
         /bin/cp /etc/mailman/aliases /etc/mail/mailman.aliases
         /usr/bin/newaliases

    In /etc/sudoers.d/mailman::

         Cmnd_Alias IMPORT_MAILMAN_ALIASES = /etc/mail/import-mailman-aliases
         apache ALL= NOPASSWD: IMPORT_MAILMAN_ALIASES
         mailman ALL= NOPASSWD: IMPORT_MAILMAN_ALIASES
         Defaults!IMPORT_MAILMAN_ALIASES !requiretty

    In the sendmail.mc file I changed::

         define(`ALIAS_FILE', `/etc/aliases')dnl

    to::

         define(`ALIAS_FILE', `/etc/aliases,/etc/mail/mailman.aliases')dnl

    so that the Mailman aliases would be in a separate file.

The main issue here is that Mailman 2 expects to receive messages from
the MTA via pipes, whereas Mailman 3 uses LMTP exclusively.  Recent
Sendmail does support LMTP, so it's a matter of configuring a stock
Sendmail.  But rather than using aliases, it needs to be configured to
relay to the LMTP port of Mailman.


.. _`mailing list or on IRC`: START.html#contact-us
.. _`Local Mail Transfer Protocol`:
   http://en.wikipedia.org/wiki/Local_Mail_Transfer_Protocol
.. _LMTP: http://www.faqs.org/rfcs/rfc2033.html
.. _`Simple Mail Transfer Protocol`:
   http://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol
.. _SMTP: http://www.faqs.org/rfcs/rfc5321.html
.. _Postfix: http://www.postfix.org
.. _`Variable Envelope Return Path`:
   http://en.wikipedia.org/wiki/Variable_envelope_return_path
.. _postconf: http://www.postfix.org/postconf.1.html
