===========
 Templates
===========

In Mailman 3.1 a new template system was introduced to allow for maximum
flexibility in the format and content of messages sent by and through Mailman.
For example, when a new member joins a list, a welcome message is sent to that
member.  The welcome message is created from a template found by a URL
associated with a template name and a context.

So if for example, you want to include links to pages on you website, you can
create a custom template, make it available via download from a URL, and then
associate that URL with a mailing list's welcome message.  Some standard
placeholders can be defined in the template, and these will be filled in by
Mailman when the welcome message is sent.

The URL itself can have placeholders, and this allows for additional
flexibility when looking up the content.


Examples
========

Let's say you have a mailing list::

    >>> ant = create_list('ant@example.com')

The standard welcome message doesn't have any links to it because by default
Mailman doesn't know about any web user interface front-end.  When Anne is
subscribed to the mailing list, she sees this plain welcome message.

    >>> anne = subscribe(ant, 'Anne')
    >>> items = get_queue_messages('virgin')
    >>> print(items[0].msg)
    MIME-Version: 1.0
    Content-Type: text/plain; charset="us-ascii"
    Content-Transfer-Encoding: 7bit
    Subject: Welcome to the "Ant" mailing list
    From: ant-request@example.com
    To: Anne Person <aperson@example.com>
    ...
    <BLANKLINE>
    Welcome to the "Ant" mailing list!
    <BLANKLINE>
    To post to this list, send your email to:
    <BLANKLINE>
      ant@example.com
    <BLANKLINE>
    You can make such adjustments via email by sending a message to:
    <BLANKLINE>
      ant-request@example.com
    <BLANKLINE>
    with the word 'help' in the subject or body (don't include the
    quotes), and you will get back a message with instructions.  You will
    need your password to change your options, but for security purposes,
    this email is not included here.  If you have forgotten your password you
    will need to click on the 'Forgot Password?' link on the login page.

Let's say though that you wanted to provide a link to a Code of Conduct in the
welcome message.  You publish both the code of conduct and the welcome message
pointing to the code on your website.  Now you can tell the mailing list to
use this welcome message instead of the default one.

    >>> call_http('http://localhost:9001/3.1/lists/ant.example.com/uris', {
    ...     'list:user:notice:welcome': 'http://localhost:8180/welcome_1.txt',
    ...     }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

The name of the template corresponding to the welcome message is
`list:user:notice:welcome` and the location of your new welcome message text
is at `http://localhost:8180/welcome_1.txt`.

Now when a new member subscribes to the mailing list, they'll see the new
welcome message.

    >>> bill = subscribe(ant, 'Bill')
    >>> items = get_queue_messages('virgin')
    >>> print(items[0].msg)
    MIME-Version: 1.0
    Content-Type: text/plain; charset="us-ascii"
    Content-Transfer-Encoding: 7bit
    Subject: Welcome to the "Ant" mailing list
    From: ant-request@example.com
    To: Bill Person <bperson@example.com>
    ...
    <BLANKLINE>
    Welcome to the "Ant" mailing list!
    <BLANKLINE>
    To post to this list, send your email to:
    <BLANKLINE>
      ant@example.com
    <BLANKLINE>
    There is a Code of Conduct for this mailing list which you can view at
    http://www.example.com/code-of-conduct.html

It's even possible to require a username and password (Basic Auth) for
retrieving the welcome message.

    >>> call_http('http://localhost:9001/3.1/lists/ant.example.com/uris', {
    ...     'list:user:notice:welcome': 'http://localhost:8180/welcome_2.txt',
    ...     'username': 'anne',
    ...     'password': 'is special',
    ...     }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

The username and password will be used to retrieve the welcome text.

    >>> cris = subscribe(ant, 'Cris')
    >>> items = get_queue_messages('virgin')
    >>> print(items[0].msg)
    MIME-Version: 1.0
    Content-Type: text/plain; charset="us-ascii"
    Content-Transfer-Encoding: 7bit
    Subject: Welcome to the "Ant" mailing list
    From: ant-request@example.com
    To: Cris Person <cperson@example.com>
    ...
    <BLANKLINE>
    I'm glad you made it!

The text is cached so subsequent uses don't necessarily need to hit the
internet.

    >>> dave = subscribe(ant, 'Dave')
    >>> items = get_queue_messages('virgin')
    >>> print(items[0].msg)
    MIME-Version: 1.0
    Content-Type: text/plain; charset="us-ascii"
    Content-Transfer-Encoding: 7bit
    Subject: Welcome to the "Ant" mailing list
    From: ant-request@example.com
    To: Dave Person <dperson@example.com>
    ...
    <BLANKLINE>
    I'm glad you made it!


Template format
===============

Mailman expects the templates to be return as content type
`text/plain; charset="UTF-8"`.

Template URLs can be any of the following schemes:

* `http://` - standard scheme supported by the requests_ library;
* `https://` - standard scheme also supported by requests_;
* `file:///` - any path on the local file system; UTF-8 contents by default;
* `mailman:///` - a path defined within the Mailman source code tree.  It is
  not recommended that you use these; they are primarily provided for
  `Mailman's internal use`_.

Generally, if a template is not defined or not found, the empty string is
used.  IOW, a missing template does not cause an error, it simply causes the
named template to be blank.


URL placeholders
================

The URLs themselves can contain placeholders, and this can be used to provide
even more flexibility in the way the template texts are retrieved.  Two common
placeholders include the List-ID and the mailing list's preferred language
code.

    >>> ant.preferred_language = 'fr'
    >>> call_http('http://localhost:9001/3.1/lists/ant.example.com/uris', {
    ...     'list:user:notice:welcome':
    ...     'http://localhost:8180/$list_id/$language/welcome_3.txt',
    ...     }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

The next person to subscribe will get a French welcome message.

    >>> dave = subscribe(ant, 'Elle')
    >>> items = get_queue_messages('virgin')
    >>> print(items[0].msg)
    MIME-Version: 1.0
    Content-Type: text/plain; charset="iso-8859-1"
    Content-Transfer-Encoding: quoted-printable
    Subject: =?iso-8859-1?q?Welcome_to_the_=22Ant=22_mailing_list?=
    From: ant-request@example.com
    To: Elle Person <eperson@example.com>
    ...
    <BLANKLINE>
    Je suis heureux que vous pouvez nous rejoindre!

Standard URL substitutions include:

* `$list_id` - The mailing list's List-ID (`ant.example.com`)
* `$listname` - The mailing list's fully qualified list name
  (`ant@example.com`)
* `$domain_name` - The mailing list's domain name (`example.com`)
* `$language` - The language code for the mailing list's preferred language
  (`fr`)


Template contexts
=================

When Mailman is looking for a template, it always searches for it in up to
three *contexts*, and you can set the template for any of these three
contexts: a mailing list, a domain, the site.

Most templates are searched first by the mailing list, then by domain, then by
site.  One notable exception is the ``domain:admin:notice:new-list`` template,
which is sent when a new mailing list is created.  Because (modulo any style
default settings) there won't be a template for the newly created mailing
list, this template is always searched for first in the domain, and then in
the site.

In fact, this illustrates a common naming scheme for templates.  The
colon-separated sections usually follow the form
``<context>:<recipient>:<type>:<name>`` where ``context`` would be "domain" or
"list, ``<recipient>`` would be "admin", "user", or "member", and ``<type>``
can be "action" or "notice".  This isn't a strict naming scheme, but it does
give you some indication as to the use of the template.  All template names
used internally by Mailman are given below.

You've already seen how the mailing list context works above.  Let's look at
the domain and site contexts next.


Domain context
--------------

Let's say you want all mailing lists in a given domain to share exactly the
same welcome message template.  Remember that Mailman will insert
substitutions into the templates themselves to customize them for each mailing
list, so in general a single template can be shared by all mailing lists in
the domain.

The first thing to do is to set the URI for the welcome message in the domain
to be shared.

    >>> call_http('http://localhost:9001/3.1/domains/example.com/uris', {
    ...     'list:user:notice:welcome':
    ...     'http://localhost:8180/welcome_4.txt',
    ...     }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

And let's create a new mailing list in this domain.

    >>> bee = create_list('bee@example.com')

Now when Anne subscribes to the Bee mailing list, she will get this
domain-wide welcome message.

    >>> anne = subscribe(bee, 'Anne')
    >>> items = get_queue_messages('virgin')
    >>> print(items[0].msg)
    MIME-Version: 1.0
    Content-Type: text/plain; charset="us-ascii"
    Content-Transfer-Encoding: 7bit
    Subject: Welcome to the "Bee" mailing list
    From: bee-request@example.com
    To: Anne Person <aperson@example.com>
    ...
    Welcome to the Bee list in the example.com domain.

So far so good.  What happens if Fred subscribes to the Ant mailing list?

    >>> fred = subscribe(ant, 'Fred')
    >>> items = get_queue_messages('virgin')
    >>> print(items[0].msg)
    MIME-Version: 1.0
    Content-Type: text/plain; charset="iso-8859-1"
    Content-Transfer-Encoding: quoted-printable
    Subject: =?iso-8859-1?q?Welcome_to_the_=22Ant=22_mailing_list?=
    From: ant-request@example.com
    To: Fred Person <fperson@example.com>
    ...
    <BLANKLINE>
    Je suis heureux que vous pouvez nous rejoindre!

Okay, that's strange!  Why did Fred get the French welcome message?  It's
because the mailing list context overrides the domain context!  Similarly, a
domain context overrides a site context.  This allows you to provide generic
templates to be used as a default, with specific overrides where necessary.

Let's delete the Ant list's override.

    >>> ant.preferred_language = 'en'
    >>> call_http('http://localhost:9001/3.1/lists/ant.example.com/uris'
    ...           '/list:user:notice:welcome',
    ...           method='DELETE')
    content-length: 0
    date: ...
    server: ...
    status: 204

Now when Gwen subscribes to the Ant list, she gets the domain's welcome
message.

    >>> gwen = subscribe(ant, 'Gwen')
    >>> items = get_queue_messages('virgin')
    >>> print(items[0].msg)
    MIME-Version: 1.0
    Content-Type: text/plain; charset="us-ascii"
    Content-Transfer-Encoding: 7bit
    Subject: Welcome to the "Ant" mailing list
    From: ant-request@example.com
    To: Gwen Person <gperson@example.com>
    ...
    <BLANKLINE>
    Welcome to the Ant list in the example.com domain.


Site context
------------

Let's say we want the same welcome template for every mailing list on our
Mailman installation.  For this we use the site context.

First, let's delete the domain context we set previously.  Note that
previously we used a `DELETE` method on the list's welcome template resource,
but we could have also done this by PATCHing an empty string for the URI,
which Mailman's REST API interprets as a deletion too.  Let's use this
approach to delete the domain welcome message.

    >>> call_http('http://localhost:9001/3.1/domains/example.com/uris', {
    ...     'list:user:notice:welcome': '',
    ...     }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

Now let's set a new welcome template URI for the site.

    >>> call_http('http://localhost:9001/3.1/uris', {
    ...     'list:user:notice:welcome':
    ...     'http://localhost:8180/welcome_5.txt',
    ...     }, method='PATCH')
    content-length: 0
    date: ...
    server: ...
    status: 204

Now Herb subscribes to both the Ant...

    >>> herb = subscribe(ant, 'Herb')
    >>> items = get_queue_messages('virgin')
    >>> print(items[0].msg)
    MIME-Version: 1.0
    Content-Type: text/plain; charset="us-ascii"
    Content-Transfer-Encoding: 7bit
    Subject: Welcome to the "Ant" mailing list
    From: ant-request@example.com
    To: Herb Person <hperson@example.com>
    ...
    <BLANKLINE>
    Yay! You joined the ant@example.com mailing list.

...and Bee mailing lists.

    >>> herb = subscribe(bee, 'Herb')
    >>> items = get_queue_messages('virgin')
    >>> print(items[0].msg)
    MIME-Version: 1.0
    Content-Type: text/plain; charset="us-ascii"
    Content-Transfer-Encoding: 7bit
    Subject: Welcome to the "Bee" mailing list
    From: bee-request@example.com
    To: Herb Person <hperson@example.com>
    ...
    <BLANKLINE>
    Yay! You joined the bee@example.com mailing list.


Templated texts
===============

All the texts that Mailman uses to create or decorate messages can be
associated with a URL.  Mailman looks up templates by name and downloads it
via that URL.  The retrieved text supports placeholders which are filled in by
Mailman.  There are a common set of placeholders most templates support:

* ``listname`` - fully qualified list name (e.g. ``ant@example.com``)
* ``list_id`` - the ``List-ID`` header (e.g. ``ant.example.com``)
* ``display_name`` - the display name of the mailing list (e.g. ``Ant``)
* ``short_listname`` - the local part of the list name (e.g. ``ant``)
* ``domain`` - the domain name part of the list name (e.g. ``example.com``)
* ``description`` - the mailing list's short description text
* ``info`` - the mailing list's longer descriptive text
* ``request_email`` - the email address for the ``-request`` alias
* ``owner_email`` - the email address for the ``-owner`` alias
* ``site_email`` - the email address to reach the owners of the site
* ``language`` - the two letter language code for the list's preferred
  language (e.g. ``en``, ``it``, ``fr``)

Other template substitutions are described below the template name listed
below.  Here are all the supported template names:

* ``domain:admin:notice:new-list``
    Sent to the administrators of any newly created mailing list.

* ``list:admin:action:post``
    Sent to the list administrators when moderator approval for a posting is
    required.

    * ``subject`` - the original ``Subject`` of the message
    * ``sender_email`` - the poster's email address
    * ``reasons`` - some reasons why the post is being held for approval

* ``list:admin:action:subscribe``
    Sent to the list administrators when moderator approval for a subscription
    request is required.

    * ``member`` - display name and email address of the subscriber

* ``list:admin:action:unsubscribe``
    Sent to the list administrators when moderator approval for an
    unsubscription request is required.

    * ``member`` - display name and email address of the subscriber

* ``list:admin:notice:subscribe``
    Sent to the list administrators to notify them when a new member has
    been subscribed.

    * ``member`` - display name and email address of the subscriber

* ``list:admin:notice:unrecognized``
    Sent to the list administrators when a bounce message in an unrecognized
    format has been received.

* ``list:admin:notice:unsubscribe``
    Sent to the list administrators to notify them when a member has been
    unsubscribed.

    * ``member`` - display name and email address of the subscriber

* ``list:member:digest:footer``
    The footer for a digest message.

* ``list:member:digest:header``
    The header for a digest message.

* ``list:member:digest:masthead``
    The digest "masthead"; i.e. a common introduction for all digest
    messages.

* ``list:member:regular:footer``
    The footer for a regular (non-digest) message.

    When personalized deliveries are enabled, these substitution variables are
    also defined:

    * ``member`` - display name and email address of the subscriber
    * ``user_email`` - the email address of the recipient
    * ``user_delivered_to`` - the case-preserved email address of the recipient
    * ``user_language`` - the description of the user's preferred language
      (e.g. "French", "English", "Italian")
    * ``user_name`` - the recipient's display name if available

* ``list:member:regular:header``
    The header for a regular (non-digest) message.

    When personalized deliveries are enabled, these substitution variables are
    also defined:

    * ``member`` - display name and email address of the subscriber
    * ``user_email`` - the email address of the recipient
    * ``user_delivered_to`` - the case-preserved email address of the recipient
    * ``user_language`` - the description of the user's preferred language
      (e.g. "French", "English", "Italian")
    * ``user_name`` - the recipient's display name if available

* ``list:user:action:subscribe``
    The message sent to subscribers when a subscription confirmation is
    required.

    * ``token`` - the unique confirmation token
    * ``subject`` - the ``Subject`` heading for the confirmation email, which
      includes the confirmation token
    * ``confirm_email`` - the email address to send the confirmation response
      to; this corresponds to the ``Reply-To`` header
    * ``user_email`` - the email address being confirmed

* ``list:user:action:unsubscribe``
    The message sent to subscribers when an unsubscription confirmation is
    required.

    * ``token`` - the unique confirmation token
    * ``subject`` - the ``Subject`` heading for the confirmation email, which
      includes the confirmation token
    * ``confirm_email`` - the email address to send the confirmation response
      to; this corresponds to the ``Reply-To`` header
    * ``user_email`` - the email address being confirmed

* ``list:user:notice:goodbye``
    The notice sent to a member when they unsubscribe from a mailing list.

* ``list:user:notice:hold``
    The notice sent to a poster when their message is being held or moderator
    approval.

    * ``subject`` - the original ``Subject`` of the message
    * ``sender_email`` - the poster's email address
    * ``reasons`` - some reasons why the post is being held for approval

* ``list:user:notice:no-more-today``
    Sent to a user when the maximum number of autoresponses has been reached
    for that day.

    * ``sender_email`` - the email address of the poster
    * ``count`` - the number of autoresponse messages sent to the user today

* ``list:user:notice:post``
    Notice sent to a poster when their message has been received by the
    mailing list.

    * ``subject`` - the ``Subject`` field of the received message

* ``list:user:notice:probe``
    A bounce probe sent to a member when their subscription has been disabled
    due to bounces.

    * ``sender_email`` - the email address of the bouncing member

* ``list:user:notice:refuse``
    Notice sent to a poster when their message has been rejected by the list's
    moderator.

    * ``request`` - the type of request being rejected
    * ``reason`` - the reason for the rejection, as provided by the list's
      moderators

* ``list:user:notice:welcome``
    The notice sent to a member when they are subscribed to the mailing list.

    * ``user_name`` - the display name of the new member
    * ``user_email`` - the email address of the new member


.. _requests: http://docs.python-requests.org/en/master/
.. _`Mailman's internal use`: https://gitlab.com/mailman/mailman/blob/master/src/mailman/utilities/i18n.py#L45
