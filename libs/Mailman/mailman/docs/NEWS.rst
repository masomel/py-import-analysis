=======================
 GNU Mailman 3 changes
=======================

Copyright (C) 1998-2017 by the Free Software Foundation, Inc.
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

Here is a history of user visible changes to Mailman.


3.1.0 -- "Between The Wheels"
=============================
(2017-05-25)

Bugs
----
 * When the mailing list's ``admin_notify_mchanges`` is True, the list owners
   now get the subscription notification.  (Closes: #1)
 * Fix the traceback that occurred when trying to convert a ``text/html``
   subpart to plaintext via the ``mimedel`` handler.  Now, a configuration
   variable ``[mailman]html_to_plain_text_command`` in the ``mailman.cfg`` file
   defines the command to use.  It defaults to ``lynx``.  (Closes: #109)
 * Confirmation messages should not be ``Precedence: bulk``.  (Closes #75)
 * Fix constraint violations on mailing list deletes affecting PostgreSQL.
   Given by Abhilash Raj.  (Closes #115)
 * ``mailman`` command with no subcommand now prints the help text.  Given by
   Abhilash Raj.  (Closes #137)
 * The MHonArc archiver must set stdin=PIPE when calling the subprocess.
   Given by Walter Doekes.
 * For now, treat ``DeliveryMode.summary_digests`` the same as
   ``.mime_digests``.
   (Closes #141).  Also, don't enqueue a particular digest if there are no
   recipients for that digest.
 * For Python versions earlier than 3.5, use a compatibility layer for a
   backported smtpd module which can accept non-UTF-8 data.  (Closes #140)
 * Bulk emails are now decorated with headers and footers.  Given by Aurélien
   Bompard.  (Closes #145)
 * Core no longer depends on the standalone ``mock`` module.  (Closes: #146)
 * The logging of moderation reasons has been fixed.  Given by Aurélien
   Bompard.
 * Collapse multiple ``Re:`` in Subject headers.  Given by Mark Sapiro.
   (Closes: #147)
 * Added Trove classifiers to setup.py.  (Closes: #152)
 * Fix the processing of subscription confirmation messages when the mailing
   list is set to confirm-then-moderate.  (Closes #114)
 * Fix ``UnicodeEncodeError`` in the hold chain when sending the authorization
   email to the mailing list moderators.  (Closes: #144)
 * Fix traceback in approved handler when the moderator password is None.
   Given by Aurélien Bompard.
 * Fix IntegrityErrors raised under PostreSQL when deleting users and
   addresses.  Given by Aurélien Bompard.
 * Allow mailing lists to have localhost names with a suffix matching the
   subcommand extensions.  Given by Aurélien Bompard.  (Closes: #168)
 * Don't traceback if a nonexistent message-id is deleted from the message
   store.  Given by Aurélien Bompard, tweaked by Barry Warsaw.  (Closes: #167)
 * Fix a bug in ``SubscriptionService.find_members()`` when searching for a
   subscribed address that is not linked to a user.  Given by Aurélien Bompard.
 * Fix a REST server crash when trying to subscribe a user without a preferred
   address.  (Closes #185)
 * Fix membership query when multiple users are subscribed to a mailing list.
   Reported by Darrell Kresge.  (Closes: #190)
 * Prevent moderation of messages held for a different list.  (Closes: #161)
 * When approving a subscription request via the REST API, for a user who is
   already a member, return an HTTP 409 Conflict code instead of the previous
   server traceback (and resulting HTTP 500 code).  (Closes: #193)
 * In decoration URIs (e.g. ``IMailingList.header_uri`` and ``.footer_uri``)
   you should now use the mailing list's List-ID instead of the
   fqdn-listname.  The latter is deprecated.  (Closes #196)
 * Trying to subscribe an address as a list owner (or moderator or nonmember)
   which is already subscribed with that role produces a server error.
   Originally given by Anirudh Dahiya.  (Closes #198)
 * Cross-posting messages held on both lists no longer fails.  (Closes #176)
 * Don't let unknown charsets crash the "approved" rule.  Given by Aurélien
   Bompard.  (Closes #203)
 * Don't let crashes in IArchiver plugins break handlers or runners.
   (Closes #208)
 * Fix "None" as display name in welcome message.  Given by Aditya Divekar.
   (Closes #194)
 * Fix ``mailman shell`` processing of ``$PYTHONSTARTUP``.  (Closes #224)
 * Fix query bug for ``SubscriptionService.find_members()`` leading to the
   incorrect number of members being returned.  Given by Aurélien Bompard.
   (Closes #227)
 * Fix header match rule suffix inflation.  Given by Aurélien Bompard.
   (Closes #226)
 * MIME digests now put the individual message/rfc822 messages inside a
   multipart/digest subpart.  (Closes #234)
 * Nonmember subscriptions are removed when one of the addresses controlled by
   a user is subscribed as a member.  Given by Aditya Divekar.  (Closes #237)
 * Email address validation is now more compliant with RFC 5321.  (Closes #266)
 * A mailing list's ``description`` must not contain newlines.  Given by
   Aurélien Bompard.  (Closes: #273)
 * Allow MailingList.info to be set using the REST API.  Given by Aurélien
   Bompard.
 * Extend header filters to also check sub-part headers.  (Closes #280)
 * Allow REST API to PUT and PATCH domain attributes.  Allows Postorius domain
   edit to work.  (Closes: #290)
 * Prevent posting from banned addresses.  Given by Aurélien Bompard.
   (Closes: #283)
 * Remove the digest mbox files after the digests are sent.  Given by Aurélien
   Bompard.  (Closes: #259)
 * Transmit the moderation reason and expose it in the REST API as the
   ``reason`` attribute.  Given by Aurélien Bompard.
 * Don't return a 500 error from the REST API when trying to handle a held
   message with defective content.  Given by Abhilash Raj.  (Closes: #256)
 * Delete subscription requests when a mailing list is deleted.  Given by
   Abhilash Raj.  (Closes: #214)
 * Messages were shunted when non-ASCII characters appeared in a mailing
   list's description.  Given by Mark Sapiro.  (Closes: #215)
 * Fix confirmation of unsubscription requests.  (Closes: #294)
 * Fix ``mailman stop`` not stopping some runners due to PEP 475 interaction.
   (Closes: #255)
 * Update documentation links for ``config.cfg`` settings.  (Closes: #306)
 * Disallow problematic characters in listnames.  (Closes: #311)
 * Forward port several content filtering fixes from the 2.1 branch.
   (Closes: #330, #331, #332 and #334)

Configuration
-------------
 * Mailing lists can now have their own header matching rules, although
   site-defined rules still take precedence.  Importing a Mailman 2.1 list
   with header matching rules defined will create them in Mailman 3, albeit
   with a few unsupported corner cases.  Definition of new header matching
   rules is not yet exposed through the REST API.  Given by Aurélien Bompard.
 * The default languages from Mailman 2.1 have been ported over.  Given by
   Aurélien Bompard.
 * There is now a configuration setting to limit the characters that can be
   used in list names.

Command line
------------
 * ``mailman create <listname@dom.ain>`` will now create missing domains
   by default.  The ``-d``/``--domain`` option is kept for backward
   compatibility, but now there is a ``-D``/``--no-domain`` option to prevent
   missing domains from being create, forcing an error in those cases.
   Given by Gurkirpal Singh.  (Closes #39)
 * ``mailman`` subcommands now properly commit any outstanding transactions.
   (Closes #223)
 * ``mailman digests`` has grown ``--verbose`` and ``-dry-run`` options.
 * ``mailman shell`` now supports readline history if you set the
   ``[shell]history_file`` variable in mailman.cfg.  Also, many useful names
   are pre-populated in the namespace of the shell.  (Closes: #228)

Database
--------
 * MySQL is now an officially supported database.  Given by Abhilash Raj.
 * Fix a problem with tracebacks when a PostgreSQL database is power cycled
   while Mailman is still running.  This ports an upstream SQLAlchemy fix to
   Mailman in lieu of a future SQLAlchemy 1.2 release.  (Closes: #313)

Interfaces
----------
 * Implement reasons for why a message is being held for moderator approval.
   Given by Aurélien Bompard, tweaked by Barry Warsaw.
 * The default ``postauth.txt`` and ``postheld.txt`` templates now no longer
   include the inaccurate admindb and confirmation urls.
 * Messages now include a ``Message-ID-Hash`` as the replacement for
   ``X-Message-ID-Hash`` although the latter is still included for backward
   compatibility.  Also be sure that all places which add the header use the
   same algorithm.  (Closes #118)
 * ``IMessageStore.delete_message()`` no longer raises a ``LookupError`` when
   you attempt to delete a nonexistent message from the message store.
 * ``ISubscriptionService.find_members()`` accepts asterisks as wildcards in
   the ``subscriber`` argument string.  Given by Aurélien Bompard.
 * ``ISubscriptionService`` now supports mass unsubscribes.  Given by Harshit
   Bansal.

Message handling
----------------
 * New DMARC mitigations have been added.  Given by Mark Sapiro.  (Closes #247)
 * New placeholders have been added for message headers and footers.  You can
   use a placeholder of the format ``$<archiver-name>_url`` to insert the
   permalink to the message in the named archiver, for any archiver enabled
   for the mailing list.  Given by Abhilash Raj.
 * The default posting chain has been modified so that the header-match chain
   and nonmember-moderation rule are processed before "hold" rules are
   processed.  This allows for better anti-spam defenses and rejecting
   non-member posts instead of always holding them for moderator review.
   Given by Aurélien Bompard.  (Closes #163)
 * Bounces can now contain rejection messages.  Given by Aurélien Bompard.
 * The ``moderation_action`` for members and nonmember can now be ``None``
   which signals falling back to the appropriate list default action,
   e.g. ``default_member_action`` and ``default_nonmember_action``.  Given by
   Aurélien Bompard.  (Closes #189)
 * Ensure that postings from alternative emails aren't held for moderator
   approval.  For example, if a user is subscribed with one email but posts
   with a second email that they control, the message should be processed as
   a posting from a member.  Given by Aditya Divekar.  (Closes #222)
 * The default message footer has been improved to include a way to
   unsubscribe via the ``-leave`` address.  Given by Francesco Ariis.

REST
----
 * REST API version 3.1 introduced.  Mostly backward compatible with version
   3.0 except that UUIDs are represented as hex strings instead of 128-bit
   integers, since the latter are not compatible with all versions of
   JavaScript.  (Closes #121)
 * REST clients must minimally support HTTP/1.1. (Closes #288)
 * Experimental Gunicorn support.  See ``contrib/gunicorn.py`` docstring for
   details.  With assistance from Eric Searcy.  (Closes #287)
 * The new template system is introduced for API 3.1.  See
   ``src/mailman/rest/docs/templates.rst`` for details.  (Closes #249)
 * When creating a user via REST using an address that already exists, but
   isn't linked, the address is linked to the new user.  Given by Aurélien
   Bompard.
 * The REST API incorrectly parsed ``is_server_owner`` values when given
   explicitly in the POST that creates a user.  (Closes #136)
 * A new top-level resource ``<api>/owners`` can be used to get the list of
   server owners as ``IUser`` s.  (Closes #135)
 * By POSTing to a user resource with an existing unlinked address, you can
   link the address to the user.  Given by Abhilash Raj.
 * Fix pagination values ``start`` and ``total_size`` in the REST API.  Given
   by Aurélien Bompard.  (Closes: #154)
 * JSON representations for held message now include a ``self_link``.
 * When ``[devmode]enabled`` is set, the JSON output is sorted.  Given by
   Aurélien Bompard.
 * A member's moderation action can be changed via the REST API.  Given by
   Aurélien Bompard.
 * Fixed a number of corner cases for the return codes when PUTing or PATCHing
   list configuration variables.  (Closes: #182)
 * Expose ``digest_send_periodic``, ``digest_volume_frequency``, and
   ``digests_enabled`` (renamed from ``digestable``) to the REST API.
   (Closes: #159)
 * Expose the "bump digest" and "send digest" functionality though the REST
   API via the ``<api>/lists/<list-id>/digest`` end-point.  GETting this
   resource returns the ``next_digest_number`` and ``volume`` as the same
   values accessible through the list's configuraiton resource.  POSTing to
   the resource with either ``send=True``, ``bump=True``, or both invokes the
   given action.
 * Global and list-centric bans can now be managed through the REST API.
   Given by Aurélien Bompard.
 * ``<api>/members/find`` accepts GET query parameters in addition to POST
   arguments.  Given by Aurélien Bompard.
 * Header match rules for individual mailing lists are now exposed in the REST
   API.  Given by Aurélien Bompard.  (Closes: #192)
 * Expose ``goodbye_message_uri`` in the REST API.  Given by Harshit Bansal.
 * New subscription requests are rejected if there is already one pending.
   With thanks to Anirudh Dahiya.  (Closes #199)
 * Expose the system pipelines and chains via ``<api>/system/pipelines`` and
   ``<api>/system/chains`` respectively.  Given by Simon Hanna.  (Closes #66)
 * Support mass unsubscription of members via ``DELETE`` on the
   ``<api>/lists/<list-id>/roster/member`` resource.  Given by Harshit
   Bansal.  (Closes #171)
 * It is now possible to merge users when creating them via REST.  When you
   POST to ``<api>/users/<address>/addresses`` and the address given in the
   ``email`` parameter already exists, instead of getting a 400 error, if you
   set ``absorb_existing=True`` in the POST data, the existing user will be
   merged into the newly created on.  Given by Aurélien Bompard.
 * Port to Falcon 1.0 (Closes #20)
 * A member's ``moderation_action`` can be reset, allowing fallback to the
   list's ``default_member_action`` by setting the attribute to the empty
   string in the REST API.  Given by Aurélien Bompard.
 * A list's ``moderator_password`` can be set via the REST API.  Given by
   Andrew Breksa.  (Closes #207)
 * The ban manager now returns a pageable, sorted sequence.  Given by Amit and
   Aurélien Bompard.  (Closes #284)
 * Query parameters now allow you to filter mailing lists by the
   ``advertised`` boolean parameter.  Given by Aurélien Bompard.
 * Only the system-enabled archivers are returned in the REST API.  Given by
   Aurélien Bompard.
 * **Backward incompatibility: mild** Held message resources now have an
   ``original_subject`` key which is the raw value of the ``Subject:`` header
   (i.e. without any RFC 2047 decoding).  The ``subject`` key is RFC 2047
   decoded.  Given by Simon Hanna.  (Closes #219)

Other
-----
 * Add official support for Python 3.5 and 3.6. (Closes #295)
 * A handful of unused legacy exceptions have been removed.  The redundant
   ``MailmanException`` has been removed; use ``MailmanError`` everywhere.
 * Drop the use of the ``lazr.smtptest`` library, which is based on the
   asynchat/asyncore-based smtpd.py stdlib module.  Instead, use the
   asyncio-based `aiosmtpd <http://aiosmtpd.readthedocs.io/>`_ package.
 * Improvements in importing Mailman 2.1 lists, given by Aurélien Bompard.
 * The ``prototype`` archiver is not web accessible so it does not have a
   ``list_url`` or permalink.  Given by Aurélien Bompard.
 * Large performance improvement in ``SubscriptionService.find_members()``.
   Given by Aurélien Bompard.
 * Rework the digest machinery, and add a new ``digests`` subcommand, which
   can be used from the command line or cron to immediately send out any
   partially collected digests, or bump the digest and volume numbers.
 * The mailing list "data directory" has been renamed.  Instead of using the
   fqdn listname, the subdirectory inside ``[paths]list_data_dir`` now uses
   the List-ID.
 * The ``mailman members`` command can now be used to display members based on
   subscription roles.  Also, the positional "list" argument can now accept
   list names or list-ids.
 * Unsubscriptions can now be confirmed and/or moderated.  (Closes #213)


3.0.0 -- "Show Don't Tell"
==========================
(2015-04-28)

Architecture
------------
 * Domains now have a list of owners, which are ``IUser`` objects, instead of
   the single ``contact_address`` they used to have.  ``IUser`` objects now
   also have a ``is_server_owner`` flag (defaulting to False) to indicate
   whether they have superuser privileges.  Give by Abhliash Raj, with fixes
   and refinements by Barry Warsaw.  (LP: #1423756)
 * Mailing list subscription policy work flow has been completely rewritten.
   It now properly supports email verification and subscription confirmation
   by the user, and approval by the moderator using unique tokens.
   ``IMailingList`` objects now have a ``subscription_policy`` attribute.
   (LP: #1095552)
 * Port the REST machinery to Falcon 0.3. (LP: #1446881)

Bugs
----
 * Fix calculation of default configuration file to use when the ``$var_dir``
   is created by ``mailman start``.  (LP: #1411435)
 * When creating a user with an email address, do not create the user record
   if the email address already exists.  Given by Andrew Stuart.
   (LP: #1418280)
 * When deleting a user via REST, make sure all linked addresses are deleted.
   Found by Andrew Stuart.  (LP: #1419519)
 * When trying to subscribe an address to a mailing list through the REST API
   where a case-differing version of the address is already subscribed, return
   a 409 error instead of a 500 error.  Found by Ankush Sharma.  (LP: #1425359)
 * ``mailman lists --domain`` was not properly handling its arguments.  Given
   by Manish Gill.  (LP: #1166911)
 * When deleting a user object, make sure their preferences are also deleted.
   Given by Abhishek.  (LP: #1418276)
 * Be sure a mailing list's acceptable aliases are deleted when the mailing
   list itself is deleted.  (LP: #1432239)
 * The built-in example ``IArchiver`` implementations now explicitly return
   None.  (LP: #1203359)
 * The test suite now runs successfully again with PostgreSQL.  Given by
   Aurélien Bompard.  (LP: #1435941)

Configuration
-------------
 * When specifying a file system path in the [paths.*] section, $cfg_file can
   be used to expand into the path of the ``-C`` option if given.  In the
   default ``[paths.dev]`` section, ``$var_dir`` is now specified relative to
   ``$cfg_file`` so that it won't accidentally be relative to the current
   working directory, if ``-C`` is given.
 * ``$cwd`` is now an additional substitution variable for the ``mailman.cfg``
   file's ``[paths.*]`` sections.  A new ``[paths.here]`` section is added,
   which puts the ``var_dir`` in ``$cwd``.  It is made the default layout.

Documentation
-------------
 * Improve the documentation describing how to run Alembic to add new schema
   migrations.  Given by Abhilash Raj.

REST
----
 * **Backward incompatible change**: The JSON representation for pending
   mailing list subscription hold now no longer includes the ``password``
   key.  Also, the ``address`` key has been renamed ``email`` for consistent
   terminology and other usage.
 * You can now view the contents of, inject messages into, and delete messages
   from the various queue directories via the ``<api>/queues`` resource.
 * You can now DELETE an address.  If the address is linked to a user, the
   user is not delete, it is just unlinked.
 * A new API is provided to support non-production testing infrastructures,
   allowing a client to cull all orphaned UIDs via ``DELETE`` on
   ``<api>/reserved/uids/orphans``.  Note that *no guarantees* of API
   stability will ever be made for resources under ``reserved``.
   (LP: #1420083)
 * Domains can now optionally be created with owners; domain owners can be
   added after the fact; domain owners can be deleted.  Also, users now have
   an ``is_server_owner`` flag as part of their representation, which defaults
   to False, and can be PUT and PATCH'd.  Given by Abhilash Raj, with fixes
   and refinements by Barry Warsaw.  (LP: #1423756)


3.0 beta 5 -- "Carve Away The Stone"
====================================
(2014-12-29)

Bugs
----
 * Fixed Unicode errors in the digest runner and when sending messages to the
   site owner as a fallback.  Given by Aurélien Bompard.  (LP: #1130957).
 * Fixed Unicode errors when a message being added to the digest has non-ascii
   characters in its payload, but no Content-Type header defining a charset.
   Given by Aurélien Bompard.  (LP: #1170347)
 * Fixed messages without a `text/plain` part crashing the `Approved` rule.
   Given by Aurélien Bompard.  (LP: #1158721)
 * Fixed getting non-ASCII filenames from RFC 2231 i18n'd messages.  Given by
   Aurélien Bompard.  (LP: #1060951)
 * Fixed `AttributeError` on MIME digest messages.  Given by Aurélien Bompard.
   (LP: #1130696)

Commands
--------
 * The `mailman conf` command no longer takes the `-t/--sort` option; the
   output is always sorted.

Configuration
-------------
 * The ``[database]migrations_path`` setting is removed.

Database
--------
 * The ORM layer, previously implemented with Storm, has been replaced by
   SQLAlchemy, thanks to the fantastic work by Abhilash Raj and Aurélien
   Bompard.  Alembic is now used for all database schema migrations.
 * The new logger `mailman.database` logs any errors at the database layer.

Development
-----------
 * Python 3.4 is now the minimum requirement.
 * You no longer have to create a virtual environment separately when running
   the test suite.  Just use `tox`.
 * You no longer have to edit `src/mailman/testing/testing.cfg` to run the
   test suite against PostgreSQL.  See `src/mailman/docs/START.rst` for
   details.

Interfaces
----------
 * The RFC 2369 headers added to outgoing messages are now added in sorted
   order.
 * Several changes to the internal API:

   - `IListManager.mailing_lists` is guaranteed to be sorted in List-ID order.
   - `IDomains.mailing_lists` is guaranteed to be sorted in List-ID order.
   - Iteration over domains via the `IDomainManager` is guaranteed to be sorted
     by `IDomain.mail_host` order.
   - `ITemporaryDatabase` interface and all implementations are removed.

REST
----
 * The Falcon Framework has replaced restish as the REST layer.  This is an
   internal change only.
 * The JSON representation `http_etag` key uses an algorithm that is
   insensitive to Python's dictionary sort order.
 * The address resource now has an additional '/user' sub-resource which can
   be used to GET the address's linked user if there is one.  This
   sub-resource also supports POST to link an unlinked address (with an
   optional 'auto_create' flag), and PUT to link the address to a different
   user.  It also supports DELETE to unlink the address.  (LP: #1312884)
   Given by Aurélien Bompard based on work by Nicolas Karageuzian.
 * The ``/3.0/system`` path is deprecated; use ``/3.0/system/versions`` to get
   the system version information.
 * You can access the system configuration via the resource path
   ``/3.0/system/configuration/<section>``.  This returns a dictionary with
   the keys being the section's variables and the values being their value
   from ``mailman.cfg`` as verbatim strings.  You can get a list of all
   section names via ``/3.0/system/configuration`` which returns a dictionary
   containing the ``http_etag`` and the section names as a sorted list under
   the ``sections`` key.  The system configuration resource is read-only.
 * Member resource JSON now include the ``member_id`` as a separate key.


3.0 beta 4 -- "Time and Motion"
===============================
(2014-04-22)

Development
-----------
 * Mailman 3 no longer uses ``zc.buildout`` and tests are now run by the
   ``nose2`` test runner.  See ``src/mailman/docs/START.rst`` for details on
   how to build Mailman and run the test suite.  Also, use ``-P`` to select a
   test pattern and ``-E`` to enable stderr debugging in runners.
 * Use the ``enum34`` package instead of ``flufl.enum``.
 * Use ``setuptools`` instead of ``distribute``, since the latter is defunct.

REST
----
 * Add ``reply_to_address`` and ``first_strip_reply_to`` as writable
   attributes of a mailing list's configuration.  (LP: #1157881)
 * Support pagination of some large collections (lists, users, members).
   [Florian Fuchs]  (LP: #1156529)
 * Expose ``hide_address`` to the ``.../preferences`` REST API.
   [Sneha Priscilla.]  (LP: #1203519)
 * Mailing lists can now individually enable or disable any archiver available
   site-wide.  [Joanna Skrzeszewska]  (LP: #1158040)
 * Addresses can be added to existing users, including display names, via the
   REST API.  [Florian Fuchs]
 * Fixed a crash in the REST server when searching for nonmembers via
   ``/find`` which we've never seen before, because those members only have an
   address record, not a user record.  This requires a small change in the API
   where the JSON response's ``address`` key now contains the URL to the
   address resource, the new ``email`` key contains the email address as a
   string, and the ``user`` key is optional.

Commands
--------
 * `mailman conf` now has a `-t/--sort` flag which sorts the output by section
   and then key.  [Karl-Aksel Puulmann and David Soto] (LP: 1162492)
 * Greatly improve the fidelity of the Mailman 2.1 list importer functionality
   (i.e. ``mailman import21``).  [Aurélien Bompard].

Configuration
-------------
 * Add support for the Exim 4 MTA.  [Stephen Turnbull]
 * When creating the initial file system layout in ``var``, e.g. via
   ``bin/mailman info``, add an ``var/etc/mailman.cfg`` file if one does not
   already exist.  Also, when initializing the system, look for that file as
   the configuration file, just after ``./mailman.cfg`` and before
   ``~/.mailman.cfg``.  (LP: #1157861)

Database
--------
 * The `bounceevent` table now uses list-ids to cross-reference the mailing
   list, to match other tables.  Similarly for the `IBounceEvent` interface.
 * Added a `listarchiver` table to support list-specific archivers.

Bugs
----
 * Non-queue runners should not create ``var/queue`` subdirectories.
   [Sandesh Kumar Agrawal] (LP: #1095422)
 * Creation of lists with upper case names should be coerced to lower case.
   (LP: #1117176)
 * Fix REST server crash on `mailman reopen` due to no interception of
   signals.  (LP: #1184376)
 * Add `subject_prefix` to the `IMailingList` interface, and clarify the
   docstring for `display_name`.  (LP: #1181498)
 * Fix importation from MM2.1 to MM3 of the archive policy.
   [Aurélien Bompard] (LP: #1227658)
 * Fix non-member moderation rule to prefer a member sender if both members
   and non-members are in the message's sender list.  [Aurélien Bompard]
   (LP: #1291452)
 * Fix IntegrityError (against PostgreSQL) when deleting a list with content
   filters.  [Aurélien Bompard]  (LP: #1117174)
 * Fix test isolation bug in ``languages.rst``.
   [Piotr Kasprzyk] (LP: #1308769)


3.0 beta 3 -- "Here Again"
==========================
(2012-12-31)

Compatibility
-------------
 * Python 2.7 is now required.  Python 2.6 is no longer officially supported.
   The code base is now also `python2.7 -3` clean, although there are still
   some warnings in 3rd party dependencies.  (LP: #1073506)

REST
----
 * **API change**: The JSON representation for held messages no longer
   includes the `data` key.  The values in this dictionary are flatted into
   the top-level JSON representation.  The `key` key is remove since it's
   redundant.  Use `message_id` for held messages, and `address` for held
   subscriptions/unsubscriptions.  The following `_mod_*` keys are inserted
   without the `_mod_` prefix:

   - `_mod_subject` -> `subject`
   - `_mod_hold_date` -> `hold_date`
   - `_mod_reason` -> `reason`
   - `_mod_sender` -> `sender`
   - `_mod_message_id` -> `message_id`

 * List styles are supported through the REST API.  Get the list of available
   styles (by name) via `.../lists/styles`.  Create a list in a specific style
   by using POST data `style_name=<style>`.  (LP: #975692)
 * Allow the getting/setting of IMailingList.subject_prefix via the REST API
   (given by Terri Oda).  (LP: #1062893)
 * Expose a REST API for membership change (subscriptions and unsubscriptions)
   moderation.  (LP: #1090753)
 * Add list_id to JSON representation for a mailing list (given by Jimmy
   Bergman).
 * The canonical resource for a mailing list (and thus its self_link) is now
   the URL with the list-id.  To reference a mailing list, the list-id url is
   preferred, but for backward compatibility, the posting address is still
   accepted.
 * You can now PUT and PATCH on user resources to change the user's display
   name or password.  For passwords, you pass in the clear text password and
   Mailman will hash it before storing.
 * You can now verify and unverify an email address through the REST API.
   POST to .../addresses/<email>/verify and .../addresses/<email>/unverify
   respectively.  The POST data is ignored.  It is not an error to verify or
   unverify an address more than once, but verifying an already verified
   address does not change its `.verified_on` date.  (LP: #1054730)
 * Deleting a user through the REST API also deletes all the user's linked
   addresses and memberships.  (LP: #1074374)
 * A user's password can be verified by POSTing to .../user/<id>/login.  The
   data must contain a single parameter `cleartext_password` and if this
   matches, a 204 (No Content) will be returned, otherwise a 403 (Forbidden)
   is returned.  (LP: #1065447)

Configuration
-------------
 * `[passlib]path` configuration variable renamed to `[passlib]configuration`.
 * Postfix-specific configurations in the `[mta]` section are moved to a
   separate file, named by the `[mta]configuration` variable.
 * In the new `postfix.cfg` file, `postfix_map_cmd` is renamed to
   `postmap_command`.
 * The default list style is renamed to `legacy-default` and a new
   `legacy-announce` style is added.  This is similar to the `legacy-default`
   except set up for announce-only lists.

Database
--------
 * The `ban` table now uses list-ids to cross-reference the mailing list,
   since these cannot change even if the mailing list is moved or renamed.
 * The following columns were unused and have been removed:

   - `mailinglist.new_member_options`
   - `mailinglist.send_reminders`
   - `mailinglist.subscribe_policy`
   - `mailinglist.unsubscribe_policy`
   - `mailinglist.subscribe_auto_approval`
   - `mailinglist.private_roster`
   - `mailinglist.admin_member_chunksize`

Interfaces
----------
 * The `IBanManager` is no longer a global utility.  Instead, you adapt an
   `IMailingList` to an `IBanManager` to manage the bans for a specific
   mailing list.  To manage the global bans, adapt ``None``.

Commands
--------
 * `bin/mailman aliases` loses the `--output`, `--format`, and `--simple`
   arguments, and adds a `--directory` argument.  This is necessary to support
   the Postfix `relay_domains` support.
 * `bin/mailman start` was passing the wrong relative path to its runner
   subprocesses when -C was given.  (LP: #982551)
 * `bin/runner` command has been simplified and its command line options
   reduced.  Now, only one `-r/--runner` option may be provided and the
   round-robin feature has been removed.

Other
-----
 * Added support for Postfix `relay_domains` setting for better virtual domain
   support.  [Jimmy Bergman].
 * Two new events are triggered on membership changes: `SubscriptionEvent`
   when a new member joins a mailing list, and an `UnsubscriptionEvent` when a
   member leaves a mailing list.  (LP: #1047286)
 * Improve the --help text for the `start`, `stop`, `restart`, and `reopen`
   subcommands.  (LP: #1035033)

Bugs
----
 * Fixed `send_goodbye_message()`.  (LP: #1091321)
 * Fixed REST server crash on `reopen` command.  Identification and test
   provided by Aurélien Bompard.  (LP: #1184376)


3.0 beta 2 -- "Freeze"
======================
(2012-09-05)

Architecture
------------
 * The link between members and the mailing lists they are subscribed to, is
   now via the RFC 2369 `list_id` instead of the fqdn listname (i.e. posting
   address).  This is because while the posting address can change if the
   mailing list is moved to a new server, the list id is fixed.
   (LP: #1024509)

   - IListManager.get_by_list_id() added.
   - IListManager.list_ids added.
   - IMailingList.list_id added.
   - Several internal APIs that accepted fqdn list names now require list ids,
     e.g. ISubscriptionService.join() and .find_members().
   - IMember.list_id attribute added; .mailing_list is now an alias that
     retrieves and returns the IMailingList.

 * `passlib`_ is now used for all password hashing instead of flufl.password.
   The default hash is `sha512_crypt`.  (LP: #1015758)
 * Internally, all datetimes are kept in the UTC timezone, however because of
   LP: #280708, they are stored in the database in naive format.
 * `received_time` is now added to the message metadata by the LMTP runner
   instead of by `Switchboard.enqueue()`.  This latter no longer depends on
   `received_time` in the metadata.
 * The `ArchiveRunner` no longer acquires a lock before it calls the
   individual archiver implementations, since not all of them need a lock.  If
   they do, the implementations must acquire said lock themselves.
 * The `news` runner and queue has been renamed to the more accurate `nntp`.
   The runner has also been ported to Mailman 3 (LP: #967409).  Beta testers
   can safely remove `$var_dir/queue/news`.
 * A mailing list's *moderator password* is no longer stored in the clear; it
   is hashed with the currently selected scheme.
 * An `AddressVerificationEvent` is triggered when an `IAddress` is verified
   or unverified.  (LP: #975698)
 * A `PasswordChangeEvent` is triggered when an `IUser`'s password changes.
   (LP: #975700)
 * When a queue runner gets an exception in its _dispose() method, a
   `RunnerCrashEvent` is triggered, which contains references to the queue
   runner, mailing list, message, metadata, and exception.  Interested parties
   can subscribe to that `zope.event` for notification.
 * Events renamed and moved:
   * `mailman.chains.accept.AcceptNotification`
   * `mailman.chains.base.ChainNotification`
   * `mailman.chains.discard.DiscardNotification`
   * `mailman.chains.hold.HoldNotification`
   * `mailman.chains.owner.OwnerNotification`
   * `mailman.chains.reject.RejectNotification`
   changed to (respectively):
   * `mailman.interfaces.chains.AcceptEvent`
   * `mailman.interfaces.chains.ChainEvent`
   * `mailman.interfaces.chains.DiscardEvent`
   * `mailman.interfaces.chains.HoldEvent`
   * `mailman.interfaces.chains.AcceptOwnerEvent`
   * `mailman.interfaces.chains.RejectEvent`
 * A `ConfigurationUpdatedEvent` is triggered when the system-wide global
   configuration stack is pushed or popped.
 * The policy for archiving has now been collapsed into a single enum, called
   ArchivePolicy.  This describes the three states of never archive, archive
   privately, and archive_publicly. (LP: #967238)

Database
--------
 * Schema migrations (LP: #971013)

   - mailinglist.include_list_post_header -> allow_list_posts
   - mailinglist.news_prefix_subject_too  -> nntp_prefix_subject_too
   - mailinglist.news_moderation          -> newsgroup_moderation
   - mailinglist.archive and mailinglist.archive_private have been collapsed
     into archive_policy.
   - mailinglist.nntp_host has been removed.
   - mailinglist.generic_nonmember_action has been removed (LP: #975696)

 * Schema migrations (LP: #1024509)
   - member.mailing_list -> list_id
 * The PostgreSQL port of the schema accidentally added a moderation_callback
   column to the mailinglist table.  Since this is unused in Mailman, it was
   simply commented out of the base schema for PostgreSQL.

REST
----
 * Expose `archive_policy` in the REST API.  Contributed by Alexander
   Sulfrian.  (LP: #1039129)

Configuration
-------------
 * New configuration variables `clobber_date` and `clobber_skew` supported in
   every `[archiver.<name>]` section.  These are used to determine under what
   circumstances a message destined for a specific archiver should have its
   `Date:` header clobbered.  (LP: #963612)
 * With the switch to `passlib`_, `[passwords]password_scheme` has been
   removed.  Instead use `[passwords]path` to specify where to find the
   `passlib.cfg` file.  See the comments in `schema.cfg` for details.
 * Configuration schema variable changes:
   * [nntp]username -> [nntp]user
   * [nntp]port (added)
 * Header check specifications in the `mailman.cfg` file have changed quite
   bit.  The previous `[spam.header.foo]` sections have been removed.
   Instead, there's a new `[antispam]` section that contains a `header_checks`
   variable.  This variable takes multiple lines of `Header: regexp` values,
   one per line.  There is also a new `jump_chain` variable which names the
   chain to jump to should any of the header checks (including the
   list-specific, and programmatically added ones) match.

Documentation
-------------
 * Some additional documentation on related components such as Postorius and
   hyperkitty have been added, given by Stephen J Turnbull.

Bug fixes
---------
 * Fixed the RFC 1153 digest footer to be compliant.  (LP: #887610)
 * Fixed a UnicodeError with non-ascii message bodies in the `approved` rule,
   given by Mark Sapiro. (LP: #949924)
 * Fixed a typo when returning the configuration file's header match checks.
   (LP: #953497)
 * List-Post should be NO when posting is not allowed. (LP: #987563)
 * Non-unicode values in msgdata broke pending requests. (LP: #1031391)
 * Show devmode in `bin/mailman info` output. (LP: #1035028)
 * Fix residual references to the old `IMailingList` archive variables.
   (LP: #1031393)

.. _`passlib`: http://packages.python.org/passlib/index.html


3.0 beta 1 -- "The Twilight Zone"
=================================
(2012-03-23)

Architecture
------------
 * Schema migrations have been implemented.
 * Implement the style manager as a utility instead of an attribute hanging
   off the `mailman.config.config` object.
 * PostgreSQL support contributed by Stephen A. Goss. (LP: #860159)
 * Separate out the RFC 2369 header adding handler.
 * Dynamically calculate the `List-Id` header instead of storing it in the
   database.  This means it cannot be changed.
 * Major redesign of the template search system, fixing LP: #788309.  $var_dir
   is now used when search for all template overrides, site, domain, or
   mailing list.  The in-tree English templates are used only as a last
   fallback.
 * Support downloading templates by URI, including mailman:// URIs.  This is
   used in welcome and goodbye messages, as well as regular and digest headers
   and footers, and supports both language and mailing list specifications.
   E.g. mailman:///test@example.com/it/welcome.txt
 * $user_password is no longer supported as a placeholder in headers and
   footers.
 * Mailing lists get multiple chains and pipelines.  For example, normal
   postings go through the `posting_chain` while messages to owners to through
   `owners_chain`.  The default `built-in` chain is renamed to
   `default-posting-chain` while the `built-in` pipeline is renamed
   `default-posting-pipeline`.
 * The experimental `maildir` runner is removed.  Use LMTP.
 * The LMTP server now requires that the incoming message have a `Message-ID`,
   otherwise it rejects the message with a 550 error.  Also, the LMTP server
   adds the `X-Message-ID-Hash` header automatically.  The `inject` cli
   command will also add the `X-Message-ID-Hash` header, but it will craft a
   `Message-ID` header first if one is missing from the injected text.  Also,
   `inject` will always set the correct value for the `original_size`
   attribute on the message object, instead of trusting a possibly incorrect
   value if it's already set.  The individual `IArchiver` implementations no
   longer set the `X-Message-ID-Hash` header.
 * The Prototype archiver now stores its files in maildir format inside of
   `$var_dir/archives/prototype`, given by Toshio Kuratomi.
 * Improved "8 mile high" document distilled by Stephen J Turnbull from the
   Pycon 2012 Mailman 3 sprint.  Also improvements to the Sphinx build given
   by Andrea Crotti (LP: #954718).
 * Pipermail has been eradicated.
 * Configuration variable `[mailman]filtered_messages_are_preservable`
   controls whether messages which have their top-level `Content-Type`
   filtered out can be preserved in the `bad` queue by list owners.
 * Configuration section `[scrubber]` removed, as is the scrubber handler.
   This handler was essentially incompatible with Mailman 3 since it required
   coordination with Pipermail to store attachments on disk.

Database
--------
 * Schema changes:
   - welcome_msg      -> welcome_message_uri
   - goodbye_msg      -> goodbye_message_uri
   - send_welcome_msg -> send_welcome_message
   - send_goodbye_msg -> send_goodbye_message
   - msg_header       -> header_uri
   - msg_footer       -> footer_uri
   - digest_header    -> digest_header_uri
   - digest_footer    -> digest_footer_uri
   - start_chain      -> posting_chain
   - pipeline         -> posting_pipeline
   - real_name        -> display_name (mailinglist, user, address)
 * Schema additions:
   - mailinglist.filter_action
   - mailinglist.owner_chain
   - mailinglist.owner_pipeline

REST
----
 * Held messages can now be moderated through the REST API.  Mailing list
   resources now accept a `held` path component.  GETing this returns all held
   messages for the mailing list.  POSTing to a specific request id under this
   url can dispose of the message using `Action` enums.
 * Mailing list resources now have a `member_count` attribute which gives the
   number of subscribed members.  Given by Toshio Kuratomi.

Interfaces
----------
 * Add property `IUserManager.members` to return all `IMembers` in the system.
 * Add property `IListmanager.name_components` which returns 2-tuples for
   every mailing list as (list_name, mail_host).
 * Remove previously deprecated `IListManager.get_mailing_lists()`.
 * `IMailTransportAgentAliases` now explicitly accepts duck-typed arguments.
 * `IRequests` interface is removed.  Now just use adaptation from
   `IListRequests` directly (which takes an `IMailingList` object).
 * `handle_message()` now allows for `Action.hold` which is synonymous with
   `Action.defer` (since the message is already being held).
 * `IListRequests.get_request()` now takes an optional `request_type`
   argument to narrow the search for the given request.
 * New `ITemplateLoader` utility.
 * `ILanguageManager.add()` returns the `ILanguage` object just created.
 * `IMailinglist.decorators` removed; it was unused
 * `IMailingList.real_name` -> `IMailingList.display_name`
 * `IUser.real_name` -> `IUser.display_name`
 * `IAddress.real_name` -> `IAddress.display_name`
 * Add property `IRoster.member_count`.

Commands
--------
 * IPython support in `bin/mailman shell` contributed by Andrea Crotti.
   (LP: #949926).
 * The `mailman.cfg` configuration file will now automatically be detected if
   it exists in an `etc` directory which is a sibling of argv0.
 * `bin/mailman shell` is an alias for `withlist`.
 * The `confirm` email command now properly handles `Re:`-like prefixes, even
   if they contain non-ASCII characters.  (LP: #685261)
 * The `join` email command no longer accepts an `address=` argument.  Its
   `digest=` argument now accepts the following values: `no` (for regular
   delivery), `mime`, or `plain`.
 * Added a `help` email command.
 * A welcome message is sent when the user confirms their subscription via
   email.
 * Global ``-C`` option now accepts an absolute path to the configuration
   file.  Given by Andrea Crotti.  (LP: #953707)

Bug fixes
---------
 * Subscription disabled probe warning notification messages are now sent
   without a `Precedence:` header.  Given by Mark Sapiro. (LP: #808821)
 * Fixed KeyError in retry runner, contributed by Stephen A. Goss.
   (LP: #872391)
 * Fixed bogus use of `bounce_processing` attribute (should have been
   `process_bounces`, with thanks to Vincent Fretin.  (LP: #876774)
 * Fix `test_moderation` for timezones east of UTC+0000, given by blacktav.
   (LP: #890675)


3.0 alpha 8 -- "Where's My Thing?"
==================================
(2011-09-23)

Architecture
------------
 * Factor out bounce detection to `flufl.bounce`.
 * Unrecognized bounces can now also be forwarded to the site owner.
 * mailman.qrunner log is renamed to mailman.runner
 * master-qrunner.lck -> master.lck
 * master-qrunner.pid -> master.pid
 * Four new events are created, and notifications are sent during mailing list
   lifecycle changes:
   - ListCreatingEvent - sent before the mailing list is created
   - ListCreatedEvent  - sent after the mailing list is created
   - ListDeletingEvent - sent before the mailing list is deleted
   - ListDeletedEvent  - sent after the mailing list is deleted
 * Four new events are created, and notifications are sent during domain
   lifecycle changes:
   - DomainCreatingEvent - sent before the domain is created
   - DomainCreatedEvent  - sent after the domain is created
   - DomainDeletingEvent - sent before the domain is deleted
   - DomainDeletedEvent  - sent after the domain is deleted
 * Using the above events, when a domain is deleted, associated mailing lists
   are deleted.  (LP: #837526)
 * IDomain.email_host -> .mail_host (LP: #831660)
 * User and Member ids are now proper UUIDs.
 * Improved the way enums are stored in the database, so that they are more
   explicitly expressed in the code, and more database efficient.

REST
----
 * Preferences for addresses, users, and members can be accessed, changed, and
   deleted through the REST interface.  Hierarchical, combined preferences for
   members, and system preferences can be read through the REST interface.
   (LP: #821438)
 * The IMailingList attribute ``host_name`` has been renamed to ``mail_host``
   for consistency.  This changes the REST API for mailing list
   resources. (LP: #787599)
 * New REST resource http://.../members/find can be POSTed to in order to find
   member records.  Optional arguments are `subscriber` (email address to
   search for), `fqdn_listname`, and `role` (i.e. MemberRole).  (LP: #799612)
 * You can now query or change a member's `delivery_mode` attribute through
   the REST API (LP: #833132).  Given by Stephen A. Goss.
 * New REST resource http://.../<domain>/lists can be GETed in order to find
   all the mailing lists in a specific domain (LP: #829765).  Given by
   Stephen A. Goss.
 * Fixed /lists/<fqdn_listname>/<role>/<email> (LP: #825570)
 * Remove role plurals from /lists/<fqdn_listname/rosters/<role>
 * Fixed incorrect error code for /members/<bogus> (LP: #821020).  Given by
   Stephen A. Goss.
 * DELETE users via the REST API.  (LP: #820660)
 * Moderators and owners can be added via REST (LP: #834130).  Given by
   Stephen A. Goss.
 * Getting the roster or configuration of a nonexistent list did not give a
   404 error (LP: #837676).  Given by Stephen A. Goss.
 * PATCHing an invalid attribute on a member did not give a 400 error
   (LP: #833376).  Given by Stephen A. Goss.
 * Getting the memberships for a non-existent address did not give a 404 error
   (LP: #848103).  Given by Stephen A. Goss.

Commands
--------
 * `bin/qrunner` is renamed to `bin/runner`.
 * `bin/mailman aliases` gains `-f` and `-s` options.
 * `bin/mailman create` no longer allows a list to be created with bogus owner
   addresses.  (LP: #778687)
 * `bin/mailman start --force` option is fixed.  (LP: #869317)

Documentation
-------------
 * Update the COPYING file to contain the GPLv3.  (LP: #790994)
 * Major terminology change: ban the terms "queue runners" and "qrunners" since
   not all runners manage queue directories.  Just call them "runners".  Also,
   the master is now just called "the master runner".

Testing
-------
 * New configuration variable in [devmode] section, called `wait` which sets
   the timeout value used in the test suite for starting up subprocesses.
 * Handle SIGTERM in the REST server so that the test suite always shuts down
   correctly.  (LP: #770328)

Other bugs and changes
----------------------
 * Moderating a message with Action.accept now sends the message. (LP: #827697)
 * Fix AttributeError triggered by i18n call in autorespond_to_sender()
   (LP: #827060)
 * Local timezone in X-Mailman-Approved-At caused test failure. (LP: #832404)
 * InvalidEmailAddressError no longer repr()'s its value.
 * Rewrote a test for compatibility between Python 2.6 and 2.7. (LP: #833208)
 * Fixed Postfix alias file generation when more than one mailing list
   exists.  (LP: #874929).  Given by Vincent Fretin.


3.0 alpha 7 -- "Mission"
========================
(2011-04-29)

Architecture
------------
 * Significant updates to the subscription model.  Members can now subscribe
   with a preferred address, and changes to that will be immediately reflected
   in mailing list subscriptions.  Users who subscribe with an explicit
   address can easily change to a different address, as long as that address
   is verified.  (LP: #643949)
 * IUsers and IMembers are now assigned a unique, random, immutable id.
 * IUsers now have created_on and .preferred_address properties.
 * IMembers now have a .user attribute for easy access to the subscribed user.
 * When created with add_member(), passwords are always stored encrypted.
 * In all interfaces, "email" refers to the textual email address while
   "address" refers to the `IAddress` object.
 * mailman.chains.base.Chain no longer self registers.
 * New member and nonmember moderation rules and chains.  This effectively
   ports moderation rules from Mailman 2 and replaces attributes such as
   member_moderation_action, default_member_moderation, and
   generic_nonmember_action.  Now, nonmembers exist as subscriptions on a
   mailing list and members have a moderation_action attribute which describes
   the disposition for postings from that address.
 * Member.is_moderated was removed because of the above change.
 * default_member_action and default_nonmember_action were added to mailing
   lists.
 * All sender addresses are registered (unverified) with the user manager by
   the incoming queue runner.  This way, nonmember moderation rules will
   always have an IAddress that they can subscribe to the list (as
   MemberRole.nonmember).
 * Support for SMTP AUTH added via smtp_user and smtp_pass configuration
   variables in the [mta] section.  (LP: #490044)
 * IEmailValidator interface for pluggable validation of email addresses.
 * .subscribe() is moved from the IAddress to the IMailingList
 * IAddresses get their registered_on attribute set when the object is created.

Configuration
-------------
 * [devmode] section gets a new 'testing' variable.
 * Added password_scheme and password_length settings  for defining the
   default password encryption scheme.
 * creator_pw_file and site_pw_file are removed.

Commands
--------
 * 'bin/mailman start' does a better job of producing an error when Mailman is
   already running.
 * 'bin/mailman status' added for providing command line status on the master
   queue runner watcher process.
 * 'bin/mailman info' now prints the REST root url and credentials.
 * mmsitepass removed; there is no more site password.

REST
----
 * Add Basic Auth support for REST API security.  (Jimmy Bergman)
 * Include the fqdn_listname and email address in the member JSON
   representation.
 * Added reply_goes_to_list, send_welcome_msg, welcome_msg,
   default_member_moderation to the mailing list's writable attributes in the
   REST service.  (Jimmy Bergman)
 * Expose the new membership model to the REST API.  Canonical member resource
   URLs are now much shorter and live in their own top-level namespace instead
   of within the mailing list's namespace.
 * /addresses/<email>/memberships gets all the memberships for a given email
   address.
 * /users is a new top-level URL under which user information can be
   accessed.  Posting to this creates new users.
 * Users can subscribe to mailing lists through the REST API.
 * Domains can be deleted via the REST API.
 * PUT and PATCH to a list configuration now returns a 204 (No Content).

Build
-----
 * Support Python 2.7. (LP: #667472)
 * Disable site-packages in buildout.cfg because of LP: #659231.
 * Don't include eggs/ or parts/ in the source tarball. (LP: #656946)
 * flufl.lock is now required instead of locknix.

Bugs fixed
----------
 * Typo in scan_message(). (LP: #645897)
 * Typo in add_member().  (LP: #710182) (Florian Fuchs)
 * Re-enable bounce detectors. (LP: #756943)
 * Clean up many pyflakes problems; ditching pylint.


3.0 alpha 6 -- "Cut to the Chase"
=================================
(2010-09-20)

Commands
--------
 * The functionality of 'bin/list_members' has been moved to
   'bin/mailman members'.
 * 'bin/mailman info' -v/--verbose output displays the file system
   layout paths Mailman is currently configured to use.

Configuration
-------------
 * You can now configure the paths Mailman uses for queue files, lock files,
   data files, etc. via the configuration file.  Define a file system 'layout'
   and then select that layout in the [mailman] section.  Default layouts
   include 'local' for putting everything in /var/tmp/mailman, 'dev' for local
   development, and 'fhs' for Filesystem Hierarchy Standard 2.3 (LP #490144).
 * Queue file directories now live in $var_dir/queues.

REST
----
 * lazr.restful has been replaced by restish as the REST publishing technology
   used by Mailman.
 * New REST API for getting all the members of a roster for a specific mailing
   list.
 * New REST API for getting and setting a mailing list's configuration.  GET
   and PUT are supported to retrieve the current configuration, and set all
   the list's writable attributes in one request.  PATCH is supported to
   partially update a mailing list's configuration.  Individual options can be
   set and retrieved by using subpaths.
 * Subscribing an already subscribed member via REST now returns a 409 HTTP
   error.  LP: #552917
 * Fixed a bug when deleting a list via the REST API.  LP: #601899

Architecture
------------
 * X-BeenThere header is removed.
 * Mailman no longer touches the Sender or Errors-To headers.
 * Chain actions can now fire Zope events in their _process()
   implementations.
 * Environment variable $MAILMAN_VAR_DIR can be used to control the var/
   directory for Mailman's runtime files.  New environment variable
   $MAILMAN_UNDER_MASTER_CONTROL is used instead of the qrunner's --subproc/-s
   option.

Miscellaneous
-------------
 * Allow X-Approved and X-Approve headers, equivalent to Approved and
   Approve. LP: #557750
 * Various test failure fixes.  LP: #543618, LP: #544477
 * List-Post header is retained in MIME digest messages.  LP: #526143
 * Importing from a Mailman 2.1.x list is partially supported.


3.0 alpha 5 -- "Distant Early Warning"
======================================
(2010-01-18)

REST
----
 * Add REST API for subscription services.  You can now:

   - list all members in all mailing lists
   - subscribe (and possibly register) an address to a mailing list
   - unsubscribe an address from mailing list

Commands
--------
 * 'bin/dumpdb' is now 'bin/mailman qfile'
 * 'bin/unshunt' is now 'bin/mailman unshunt'
 * Mailman now properly handles the '-join', '-leave', and '-confirm' email
   commands and sub-addresses.  '-subscribe' and '-unsubscribe' are aliases
   for '-join' and '-leave' respectively.

Configuration
-------------
 * devmode settings now live in their own [devmode] section.
 * Mailman now searches for a configuration file using this search order.  The
   first file that exists is used.

   - -C config command line argument
   - $MAILMAN_CONFIG_FILE environment variable
   - ./mailman.cfg
   - ~/.mailman.cfg
   - /etc/mailman.cfg


3.0 alpha 4 -- "Vital Signs"
============================
(2009-11-28)

Commands
--------
 * 'bin/inject' is now 'bin/mailman inject', with some changes
 * 'bin/mailmanctl' is now 'bin/mailman start|stop|reopen|restart'
 * 'bin/mailman version' is added (output same as 'bin/mailman --version')
 * 'bin/mailman members' command line arguments have changed.  It also
   now ignores blank lines and lines that start with #.  It also no longer
   quits when it sees an address that's already subscribed.
 * 'bin/withlist' is now 'bin/mailman withlist', and its command line
   arguments have changed.
 * 'bin/mailman lists' command line arguments have changed.
 * 'bin/genaliases' is now 'bin/mailman aliases'

Architecture
------------
 * A near complete rewrite of the low-level SMTP delivery machinery.  This
   greatly improves readability, testability, reuse and extensibility.  Almost
   all the old functionality has been retained.  The smtp_direct.py handler is
   gone.
 * Refactor model objects into the mailman.model subpackage.
 * Refactor most of the i18n infrastructure into a separate flufl.i18n package.
 * Switch from setuptools to distribute.
 * Remove the dependency on setuptools_bzr
 * Do not create the .mo files during setup.

Configuration
-------------
 * All log files now have a '.log' suffix by default.
 * The substitution placeholders in the verp_format configuration variable
   have been renamed.
 * Add a devmode configuration variable that changes some basic behavior.
   Most importantly, it allows you to set a low-level SMTP recipient for all
   mail for testing purposes.  See also devmode_recipient.


3.0 alpha 3 -- "Working Man"
============================
(2009-08-21)

Configuration
-------------
 * Configuration is now done through lazr.config.  Defaults.py is
   dead.  lazr.config files are essentially hierarchical ini files.
 * Domains are now stored in the database instead of in the configuration file.
 * pre- and post- initialization hooks are now available to plugins.  Specify
   additional hooks to run in the configuration file.
 * Add the environment variable $MAILMAN_CONFIG_FILE which overrides the -C
   command line option.
 * Make LMTP more compliant with Postfix docs (Patrick Koetter)
 * Added a NullMTA for mail servers like Exim which just work automatically.

Architecture
------------
 * 'bin/mailman' is a new super-command for managing Mailman from the command
   line.  Some older bin scripts have been converted, with more to come.
 * Mailman now has an administrative REST interface which can be used to get
   information from and manage Mailman remotely.
 * Back port of Mailman 2.1's limit on .bak file restoration.  After 3
   restores, the file is moved to the bad queue, with a .psv extension. (Mark
   Sapiro)
 * Digest creation is moved into a new queue runner so it doesn't block main
   message processing.

Other changes
-------------
 * bin/make_instance is no longer necessary, and removed
 * The debug log is turned up to info by default to reduce log file spam.

Building and installation
-------------------------
 * All doc tests can now be turned into documentation, via Sphinx.  Just run
   bin/docs after bin/buildout.


3.0 alpha 2 -- "Grand Designs"
==============================
(03-Jan-2009)

Licensing
---------

 * Mailman 3 is now licensed under the GPLv3.

Bug fixes
---------

 * Changed bin/arch to attempt to open the mbox before wiping the old
   archive. Launchpad bug #280418.

 * Added digest.mbox and pending.pck to the 'list' files checked by
   check_perms. Launchpad bug #284802.

Architecture
------------

 * Converted to using zope.testing as the test infrastructure.  Use bin/test
   now to run the full test suite.
   <http://pypi.python.org/pypi/zope.testing/3.7.1>
 * Partially converted to using lazr.config as the new configuration
   regime.  Not everything has been converted yet, so some manual editing
   of mailman/Defaults.py is required.  This will be rectified in future
   versions.  <http://launchpad.net/lazr.config>
 * All web-related stuff is moved to its own directory, effectively moving
   it out of the way for now.
 * The email command infrastructure has been reworked to play more nicely
   with the plug-in architecture.  Not all commands have yet been
   converted.

Other changes
-------------

 * The LMTP server now properly calculates the message's original size.
 * For command line scripts, -C names the configuration file to use.  For
   convenient testing, if -C is not given, then the environment variable
   MAILMAN_CONFIG_FILE is consulted.
 * Support added for a local MHonArc archiver, as well as archiving
   automatically in the remote Mail-Archive.com service.
 * The permalink proposal for supporting RFC 5064 has been adopted.
 * Mailing lists no longer have a .web_page_url attribute; this is taken from
   the mailing list's domain's base_url attribute.
 * Incoming MTA selection is now taken from the config file instead of
   plugins.  An MTA for Postfix+LMTP is added.  bin/genaliases works again.
 * If a message has no Message-ID, the stock archivers will return None for
   the permalink now instead of raising an assertion.
 * IArchiver no longer has an is_enabled property; this is taken from the
   configuration file now.

Installation
------------

 * Python 2.6 is the minimal requirement.
 * Converted to using zc.buildout as the build infrastructure.  See
   docs/ALPHA.txt for details.
   <http://pypi.python.org/pypi/zc.buildout/1.1.1>


3.0 alpha 1 -- "Leave That Thing Alone"
=======================================
(08-Apr-2008)

User visible changes
--------------------

 * So called 'new style' subject prefixing is the default now, and the only
   option.  When a list's subject prefix is added, it's always done so before
   any Re: tag, not after.  E.g. '[My List] Re: The subject'.
 * RFC 2369 headers List-Subscribe and List-Unsubscribe now use the preferred
   -join and -leave addresses instead of the -request address with a subject
   value.

Configuration
-------------

 * There is no more separate configure; make; make install step. Mailman 3.0
   is a setuptools package.
 * Mailman can now be configured via a 'mailman.cfg' file which lives in
   $VAR_PREFIX/etc.  This is used to separate the configuration from the
   source directory.  Alternative configuration files can be specified via
   -C/--config for most command line scripts.  mailman.cfg contains Python
   code.  mm_cfg.py is no more.  You do not need to import Defaults.py in
   etc/mailman.cfg.  You should still consult Defaults.py for the list of site
   configuration variables available to you.

   See the etc/mailman.cfg.sample file.
 * PUBLIC_ARCHIVE_URL and DEFAULT_SUBJECT_PREFIX now takes $-string
   substitutions instead of %-string substitutions.  See documentation in
   Defaults.py.in for details.
 * Message headers and footers now only accept $-string substitutions;
   %-strings are no longer supported.  The substitution variable
   '_internal_name' has been removed; use $list_name or $real_name
   instead.  The substitution variable $fqdn_listname has been added.
   DEFAULT_MSG_FOOTER in Defaults.py.in has been updated accordingly.
 * The KNOWN_SPAMMERS global variable is replaced with HEADER_MATCHES.  The
   mailing list's header_filter_rules variable is replaced with header_matches
   which has the same semantics as HEADER_MATCHES, but is list-specific.
 * DEFAULT_MAIL_COMMANDS_MAX_LINES -> EMAIL_COMMANDS_MAX_LINES
 * All SMTP_LOG_* templates use $-strings and all consistently write the
   Message-ID as the first item in the log entry.
 * DELIVERY_MODULE now names a handler, not a module (yes, this is a
   misnomer, but it will likely change again before the final release).

Architecture
------------

 * Internally, all strings are Unicodes.
 * Implementation of a chain-of-rules based approach for deciding whether a
   message should initially be accepted, held for approval, rejected/bounced,
   or discarded.  This replaces most of the disposition handlers in the
   pipeline.  The IncomingRunner now only processes message through the rule
   chains, and once accepted, places the message in a new queue processed by
   the PipelineRunner.
 * Substantially reworked the entire queue runner process management,
   including mailmanctl, a new master script, and the qrunners.  This should
   be much more robust and reliable now.
 * The Storm ORM is used for data storage, with the SQLite backend as the
   default relational database.
 * Zope interfaces are used to describe the major components.
 * Users are now stored in a unified database, and shared across all mailing
   lists.
 * Mailman's web interface is now WSGI compliant.  WSGI is a Python standard
   (PEP 333) allowing web applications to be (more) easily integrated with any
   number of existing Python web application frameworks.  For more information
   see:

   http://www.wsgi.org/wsgi
   http://www.python.org/dev/peps/pep-0333/

   Mailman can still be run as a traditional CGI program of course.
 * Mailman now provides an LMTP server for more efficient integration with
   supporting mail servers (e.g. Postfix, Sendmail).  The Local Mail Transport
   Protocol is defined in RFC 2033:

   http://www.faqs.org/rfcs/rfc2033.html
 * Virtual domains are now fully supported in that mailing lists of the same
   name can exist in more than one domain.  This is accomplished by renaming
   the lists/ and archives/ subdirectories after the list's posting address.
   For example, data for list foo in example.com and list foo in example.org
   will be stored in lists/foo@example.com and lists/foo@example.org.

   For Postfix or manual MTA users, you will need to regenerate your mail
   aliases.  Use bin/genaliases.

   VIRTUAL_HOST_OVERVIEW has been removed, effectively Mailman now operates
   as if it were always enabled.  If your site has more than one domain,
   you must configure all domains by using add_domain() in your
   etc/mailman.cfg flie (see below -- add_virtual() has been removed).
 * If you had customizations based on Site.py, you will need to re-implement
   them.  Site.py has been removed.
 * The site list is no more.  You can remove your 'mailman' site list unless
   you want to retain it for other purposes, but it is no longer used (or
   required) by Mailman.  You should set NO_REPLY_ADDRESS to an address that
   throws away replies, and you should set SITE_OWNER_ADDRESS to an email
   address that reaches the person ultimately responsible for the Mailman
   installation.  The MAILMAN_SITE_LIST variable has been removed.
 * qrunners no longer restart on SIGINT; SIGUSR1 is used for that now.

Internationalization Big Changes
--------------------------------

 * Translators should work only on messages/<lang>/LC_MESSAGES/mailman.po.
   Templates files are generated from mailman.po during the build process.

New Features
------------

 * Confirmed member change of address is logged in the 'subscribe' log, and if
   admin_notify_mchanges is true, a notice is sent to the list owner using a
   new adminaddrchgack.txt template.
 * There is a new list attribute 'subscribe_auto_approval' which is a list of
   email addresses and regular expressions matching email addresses whose
   subscriptions are exempt from admin approval. RFE 403066.

Command line scripts
--------------------

 * Most scripts have grown a -C/--config flag to allow you to specify a
   different configuration file.  Without this, the default etc/mailman.cfg
   file will be used.
 * the -V/--virtual-host-overview switch in list_lists has been removed, while
   -d/--domain and -f/--full have been added.
 * bin/newlist is renamed bin/create_list and bin/rmlist is renamed
   bin/remove_list.  Both take fully-qualified list names now (i.e. the list's
   posting address), but also accept short names, in which case the default
   domain is used.  newlist's -u/--urlhost and -e/--emailhost switches have
   been removed.  The domain that the list is being added to must already
   exist.
 * Backport the ability to specify additional footer interpolation variables
   by the message metadata 'decoration-data' key.

Bug fixes and other patches
---------------------------

 * Removal of DomainKey/DKIM signatures is now controlled by Defaults.py
   mm_cfg.py variable REMOVE_DKIM_HEADERS (default = No).
 * Queue runner processing is improved to log and preserve for analysis in the
   shunt queue certain bad queue entries that were previously logged but lost.
   Also, entries are preserved when an attempt to shunt throws an exception
   (1656289).
 * The processing of Topics regular expressions has changed. Previously the
   Topics regexp was compiled in verbose mode but not documented as such which
   caused some confusion.  Also, the documentation indicated that topic
   keywords could be entered one per line, but these entries were not handled
   properly.  Topics regexps are now compiled in non-verbose mode and multi-
   line entries are 'ored'.  Existing Topics regexps will be converted when
   the list is updated so they will continue to work.
 * The List-Help, List-Subscribe, and List-Unsubscribe headers were
   incorrectly suppressed in messages that Mailman sends directly to users.
 * The 'adminapproved' metadata key is renamed 'moderator_approved'.
