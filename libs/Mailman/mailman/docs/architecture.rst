=============================
 Mailman 3 Core architecture
=============================

This is a brief overview of the internal architecture of the Mailman 3 core
delivery engine.  You should start here if you want to understand how Mailman
works at the 1000 foot level.  Another good source of architectural
information is available in the chapter written by Barry Warsaw for the
`Architecture of Open Source Applications`_.


User model
==========

Every major component of the system is defined by an interface.  Look through
``src/mailman/interfaces`` for an understanding of the system components.
Mailman objects which are stored in the database, are defined by *model*
classes.  Objects such as *mailing lists*, *users*, *members*, and *addresses*
are primary objects within the system.

The *mailing list* is the central object which holds all the configuration
settings for a particular mailing list.  A mailing list is associated with a
*domain*, and all mailing lists are managed (i.e. created, destroyed, looked
up) via the *mailing list manager*.

*Users* represent people, and have a *user id* and a *display name*.  Users
are linked to *addresses* which represent a single email address.  One user
can be linked to many addresses, but an address is only linked to one user.
Addresses can be *verified* or *not verified*.  Mailman will deliver email
only to *verified* addresses.

Users and addresses are managed by the *user manager*.

A *member* is created by linking a *subscriber* to a mailing list.
Subscribers can be:

* A user, which become members through their *preferred address*.
* An address, which can be linked or unlinked to a user, but must be verified.

Members also have a *role*, representing regular members, digest members, list
owners, and list moderators.  Members can even have the *non-member* role
(i.e. people not yet subscribed to the mailing list) for various moderation
purposes.


Process model
=============

Messages move around inside the Mailman system by way of *queue* directories
managed by the *switchboard*.  For example, when a message is first received
by Mailman, it is moved to the *in* (for "incoming") queue.  During the
processing of this message, it -or copies of it- may be moved to other queues
such as the *out* queue (for outgoing email), the *archive* queue (for sending
to the archivers), the *digest* queue (for composing digests), etc.

A message in a queue is represented by a single file, a ``.pck`` file.  This
file contains two objects, serialized as `Python pickles`_.  The first object
is the message being processed, already parsed into a `more efficient internal
representation`_.  The second object is a metadata dictionary that records
additional information about the message as it is being processed.

``.pck`` files only exist for messages moving between different system queues.
There is no ``.pck`` file for messages while they are actively being
processed.

Each queue directory is associated with a *runner* process which wakes up
every so often.  When the runner wakes up, it examines all the ``.pck`` files
in FIFO order, deserializing the message and metadata objects, and processing
them.  If the message needs further processing in a different queue, it will
be re-serialized back into a ``.pck`` file.  If not (e.g. because processing
of the message is complete), then no ``.pck`` file is written.

The Mailman system uses a few other runners which don't process messages in a
queue.  You can think of these as fairly typical server process, and examples
include the LMTP server, and the HTTP server for processing REST commands.

All of the runners are managed by a *master watcher* process.  When you type
``mailman start`` you are actually starting the master.  Based on
configuration options, the master will start the appropriate runners as
subprocesses, and it will watch for the clean exiting of these subprocesses
when ``mailman stop`` is called.


Rules and chains
================

When a message is first received for posting to a mailing list, Mailman
processes the message to determine whether the message is appropriate for the
mailing list.  If so, it *accepts* the message and it gets posted.  Mailman
can *discard* the message so that no further processing occurs.  Mailman can
also *reject* the message, bouncing it back to the original sender, usually
with some indication of why the message was rejected.  Or, Mailman can *hold*
the message for moderator approval.

*Moderation* is the phase of processing that determines which of the above
four dispositions will occur for the newly posted message.  Moderation does
not generally change the message, but it may record information in the
metadata dictionary.  Moderation is performed by the *in* queue runner.

Each step in the moderation phase applies a *rule* to the message and asks
whether the rule *hits* or *misses*.  Each rule is linked to an *action* which
is taken if the rule hits (i.e. matches).  If the rule misses (i.e. doesn't
match), then the next rule is tried.  All of the rule/action links are strung
together sequentially into a *chain*, and every mailing list has a *start
chain* where rule processing begins.

Actually, every mailing list has *two* start chains, one for regular postings
to the mailing list, and another for posting to the owners of the mailing
list.

To recap: when a message comes into Mailman for posting to a mailing list, the
incoming runner finds the destination mailing list, determines whether the
message is for the entire list membership, or the list owners, and retrieves
the appropriate start chain.  The message is then passed to the chain, where
each link in the chain first checks to see if its rule matches, and if so, it
executes the linked action.  This action is usually one of *accept*, *reject*,
*discard*, and *hold*, but other actions are possible, such as executing a
function, deferring action, or jumping to another chain.

As you might imagine, you can write new rules, compose them into new chains,
and configure a mailing list to use your custom chain when processing the
message during the moderation phase.


Pipeline of handlers
====================

Once a message is accepted for posting to the mailing list, the message is
usually modified in a number of different ways.  For example, some message
headers may be added or removed, some MIME parts might be scrubbed, added, or
rearranged, and various informative headers and footers may be added to the
message.

The process of preparing the message for the list membership (as well as the
digests, archivers, and NNTP) falls to the *pipeline of handlers* managed by
the *pipeline* queue.

The pipeline of handlers is similar to the processing chain, except here, a
handler can make any modifications to the message it wants, and there is no
rule decision or action.  The message and metadata simply flow through a
sequence of handlers arranged in a named pipeline.  Some of the handlers
modify the message in ways described above, and others copy the message to the
outgoing, NNTP, archiver, or digester queues.

As with chains, each mailing list has two pipelines, one for posting to the
list membership, and the other for posting to the list's owners.

Of course, you can define new handlers, compose them into new pipelines, and
change a mailing list's pipelines.


Integration and control
=======================

Humans and external programs can interact with a running Core system in may
different ways.  There's an extensive command line interface that provides
useful options to a system administrator.  For external applications such as
the Postorius web user interface, and the HyperKitty archiver, the
`administrative REST API <rest-api>` is the most common way to get information
into and out of the Core.

**Note**: The REST API is an administrative API and as such it must not be
exposed to the public internet.  By default, the REST server only listens on
``localhost``.

Internally, the Python API is extensive and well-documented.  Most objects in
the system are accessed through the `Zope Component Architecture`_ (ZCA).  If
your Mailman installation is importable, you can write scripts directly
against the internal public Python API.


Other bits and pieces
=====================

There are lots of other pieces to the Mailman puzzle, such as the set of core
functionality (logging, initialization, event handling, etc.), mailing list
*styles*, the API for integrating external archivers and mail servers.  The
database layer is an critical piece, and Mailman has an extensive set of
command line commands, and email commands.

Almost the entire system is documented in these pages, but it maybe be a bit
of a spelunking effort to find it.  Improvements are welcome!


.. _`Architecture of Open Source Applications`: http://www.aosabook.org/en/mailman.html
.. _`Python pickles`: http://docs.python.org/3/library/pickle.html
.. _`more efficient internal representation`: https://docs.python.org/3/library/email.html
.. _`Zope Component Architecture`: https://pypi.python.org/pypi/zope.component
