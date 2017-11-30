===========================
 Contributing to Mailman 3
===========================

Copyright (C) 2008-2017 by the Free Software Foundation, Inc.


How to contribute
=================

We accept `merge requests`_ and `bug reports`_ on GitLab.  We prefer if every
merge request is linked to a bug report, because we can more easily manage the
priority of bug reports.  For more substantial contributions, we may ask you
to sign a `copyright assignment`_ to the Free Software Foundation, the owner
of the GNU Mailman copyright.  If you'd like to jump start your copyright
assignment, please contact the GNU Mailman `steering committee`_.

Please read the :doc:`STYLEGUIDE` for required coding style guidelines.


Contact Us
==========

Contributions of code, problem reports, and feature requests are welcome.
Please submit bug reports on the Mailman bug tracker at
https://gitlab.com/mailman/mailman/issues (you need to have a login on GitLab
to do so).  You can also send email to the mailman-developers@python.org
mailing list, or ask on IRC channel ``#mailman`` on Freenode.


Get the sources
===============

The Mailman 3 source code is version controlled using Git. You can get a
local copy by running this command::

    $ git clone https://gitlab.com/mailman/mailman.git

or if you have a GitLab account and prefer ssh::

    $ git clone git@gitlab.com:mailman/mailman.git


Testing Mailman 3
=================

To run the Mailman test suite, just use the `tox`_ command::

    $ tox

`tox` creates a virtual environment (virtualenv_) for you, installs all the
dependencies into that virtualenv, and runs the test suite from that
virtualenv.  By default it does not use the `--system-site-packages` so it
downloads everything from the `Python Cheeseshop`_.

A bare ``tox`` command will try to run several test suites, which might take a
long time, and/or require versions of Python or other components you might not
have installed.  You can run ``tox -l`` to list the test suite *environments*
available.  Very often, when you want to run the full test suite in the
quickest manner with components that should be available everywhere, run one
of these command, depending on which version of Python 3 you have::

    $ tox -e py36-nocov
    $ tox -e py35-nocov
    $ tox -e py34-nocov

You can run individual tests in any given environment by providing additional
positional arguments.  For example, to run only the tests that match a
specific pattern::

    $ tox -e py35-nocov -- -P user

You can see all the other arguments supported by the test suite by running::

    $ tox -e py35-nocov -- --help

You also have access to the virtual environments created by tox, and you can
use this run the virtual environment's Python executable, or run the
``mailman`` command locally, e.g.::

    $ .tox/py35-nocov/bin/python
    $ .tox/py35-nocov/bin/mailman --help

If you want to set up the virtual environment without running the full test
suite, you can do this::

    $ tox -e py35-nocov --notest -r


Testing with PostgreSQL and MySQL
=================================

By default, the test suite runs with the built-in SQLite database engine.  If
you want to run the full test suite against the PostgreSQL or MySQL databases,
set the database up as described in :doc:`database`.

For PostgreSQL, then create a `postgres.cfg` file any where you want.  This
`postgres.cfg` file will contain the ``[database]`` section for PostgreSQL,
e.g.::

    [database]
    class: mailman.database.postgresql.PostgreSQLDatabase
    url: postgres://myuser:mypassword@mypghost/mailman

Then run the test suite like so::

    $ MAILMAN_EXTRA_TESTING_CFG=/path/to/postgres.cfg tox -e py35-pg

You can combine these ways to invoke Mailman, so if you want to run an
individual test against PostgreSQL, you could do::

    $ MAILMAN_EXTRA_TESTING_CFG=/path/to/postgres.cfg tox -e py35-pg -- -P user

Note that the path specified in `MAILMAN_EXTRA_TESTING_CFG` must be an
absolute path or some tests will fail.


Building for development
========================

To build Mailman for development purposes, you can create a virtual
environment outside of tox.  You need to have the `virtualenv`_ program
installed, or you can use Python 3's built-in `pyvenv`_ command.

First, create a virtual environment (venv).  The directory you install the
venv into is up to you, but for purposes of this document, we'll install it
into ``/tmp/mm3``::

    $ python3 -m venv /tmp/mm3

Now, activate the virtual environment and set it up for development::

    % source /tmp/mm3/bin/activate
    % python setup.py develop

Sit back and have some Kombucha while you wait for everything to download and
install.


Building the documentation
==========================

To build the documentation, you need some additional dependencies.  The only
one you probably need from your OS vendor is `graphiz`.  E.g. On Debian or
Ubuntu, you can do::

    $ sudo apt install graphiz

All other dependencies should be automatically installed as needed.  Build the
documentation by running::

    $ tox -e docs

Then visit::

    build/sphinx/html/index.html


Mailman Shell
=============

This documentation has examples which use the Mailman shell to interact with
Mailman.  To start the shell type ``mailman shell`` in your terminal.

There are some testings functions which need to be imported first before you
use them. They can be imported from the modules available in
``mailman.testing``.  For example, to use ``dump_list`` you first need to
import it from the ``mailman.testing.documentation`` module.

.. Of course, *this* doctest doesn't have these preloaded...
   >>> from zope.component import getUtility
   >>> from mailman.interfaces.listmanager import IListManager

The shell automatically initializes the Mailman system, loads all the
available interfaces, and configures the `Zope Component Architecture`_ (ZCA)
which is used to access all the software components in Mailman.  So for
example, if you wanted to get access to the list manager component, you could
do::

    $ mailman shell
    Welcome to the GNU Mailman shell

    >>> list_manager = getUtility(IListManager)


Related projects
================

What you are looking at right now is the Mailman Core.  It's "just" the
message delivery engine, but it's designed to work with a web user interface
for list members and administrators, and an archiver.  The GNU Mailman project
also develops a web ui and archiver, but these are available in separate git
repositories.


Mailman Web UI
--------------

The Mailman 3 web UI, called *Postorius*, interfaces to core Mailman engine
via the REST client API.  This architecture makes it possible for users with
other needs to adapt the web UI, or even replace it entirely, with a
reasonable amount of effort.  However, as a core feature of Mailman, the web
UI emphasizes usability over modularity at first, so most users should use the
web UI described here.  Postorius_ is a Django_ application.


The Archiver
~~~~~~~~~~~~

In Mailman 3, the archivers are decoupled from the Core.  Instead, Mailman 3
provides a simple, standard interface for third-party archiving tools and
services.  For this reason, Mailman 3 defines a formal interface to insert
messages into any of a number of configured archivers, using whatever protocol
is appropriate for that archiver.  Summary, search, and retrieval of archived
posts are handled by a separate application.

A new archive UI called `HyperKitty`_, based on the `notmuch mail indexer`_
was prototyped at the `Pycon 2012 sprint`_ by Toshio Kuratomi.  The HyperKitty
archiver is very loosely coupled to Mailman 3 core.  In fact, any email
application that speaks LMTP or SMTP will be able to use HyperKitty.
HyperKitty is also a Django application.


REST API Python bindings
~~~~~~~~~~~~~~~~~~~~~~~~

Mailman 3 provides a REST API for administrative purposes, and this is used by
both HyperKitty and Postorius.  You can of course use any HTTP client to speak
to it, but we provide official Python bindings (for both Python 2 and 3) in a
package we call `mailman.client`_.


.. _`merge requests`: https://gitlab.com/mailman/mailman/merge_requests
.. _`bug reports`: https://gitlab.com/mailman/mailman/issues
.. _`copyright assignment`: https://www.fsf.org/licensing/assigning.html/?searchterm=copyright%20assignment
.. _`steering committee`: mailto:mailman-cabal@python.org
.. _tox: https://testrun.org/tox/latest/
.. _`Zope Component Architecture`: https://pypi.python.org/pypi/zope.component
.. _`Postorius`: https://gitlab.com/mailman/postorius
.. _`Django`: http://djangoproject.org/
.. _`HyperKitty`: https://gitlab.com/mailman/hyperkitty
.. _`notmuch mail indexer`: http://notmuchmail.org
.. _`mailman.client`: https://gitlab.com/mailman/mailmanclient
.. _`Pycon 2012 sprint`: https://us.pycon.org/2012/community/sprints/projects/
.. _`Python Cheeseshop`: http://pypi.python.org/pypi
.. _`virtualenv`: http://www.virtualenv.org/en/latest/
.. _`pyvenv`: https://docs.python.org/3/library/venv.html
