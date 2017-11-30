==========================
Operating on mailing lists
==========================

The ``shell`` (alias: ``withlist``) command is a pretty powerful way to
operate on mailing lists from the command line.  This command allows you to
interact with a list at a Python prompt, or process one or more mailing lists
through custom made Python functions.


Getting detailed help
=====================

Because ``withlist`` is so complex, you need to request detailed help.
::

    >>> from mailman.commands.cli_withlist import Withlist
    >>> command = Withlist()

    >>> class FakeArgs:
    ...     interactive = False
    ...     run = None
    ...     details = True
    ...     listname = []

    >>> class FakeParser:
    ...     def error(self, message):
    ...         print(message)
    >>> command.parser = FakeParser()

    >>> args = FakeArgs()
    >>> command.process(args)
    This script provides you with a general framework for interacting with a
    mailing list.
    ...


Running a command
=================

By putting a Python function somewhere on your ``sys.path``, you can have
``withlist`` call that function on a given mailing list.  The function takes a
single argument, the mailing list.
::

    >>> import os, sys
    >>> old_path = sys.path[:]
    >>> sys.path.insert(0, config.VAR_DIR)

    >>> with open(os.path.join(config.VAR_DIR, 'showme.py'), 'w') as fp:
    ...     print("""\
    ... def showme(mailing_list):
    ...     print("The list's name is", mailing_list.fqdn_listname)
    ...
    ... def displayname(mailing_list):
    ...     print("The list's display name is", mailing_list.display_name)
    ... """, file=fp)

If the name of the function is the same as the module, then you only need to
name the function once.

    >>> mlist = create_list('aardvark@example.com')
    >>> args.details = False
    >>> args.run = 'showme'
    >>> args.listname = 'aardvark@example.com'
    >>> command.process(args)
    The list's name is aardvark@example.com

The function's name can also be different than the modules name.  In that
case, just give the full module path name to the function you want to call.

    >>> args.run = 'showme.displayname'
    >>> command.process(args)
    The list's display name is Aardvark


Multiple lists
==============

You can run a command over more than one list by using a regular expression in
the `listname` argument.  To indicate a regular expression is used, the string
must start with a caret.
::

    >>> mlist_2 = create_list('badger@example.com')
    >>> mlist_3 = create_list('badboys@example.com')

    >>> args.listname = '^.*example.com'
    >>> command.process(args)
    The list's display name is Aardvark
    The list's display name is Badboys
    The list's display name is Badger

    >>> args.listname = '^bad.*'
    >>> command.process(args)
    The list's display name is Badboys
    The list's display name is Badger

    >>> args.listname = '^foo'
    >>> command.process(args)


Error handling
==============

You get an error if you try to run a function over a non-existent mailing
list.

    >>> args.listname = 'mystery@example.com'
    >>> command.process(args)
    No such list: mystery@example.com

You also get an error if no mailing list is named.

    >>> args.listname = None
    >>> command.process(args)
    --run requires a mailing list name


Interactive use
===============

You can also get an interactive prompt which allows you to inspect a live
Mailman system directly.  Through the ``mailman.cfg`` file, you can set the
prompt and banner, and you can choose between the standard Python REPL_ or
IPython.

If the `GNU readline`_ library is available, it will be enabled automatically,
giving you command line editing and other features.  You can also set the
``[shell]history_file`` variable in the ``mailman.cfg`` file and when the
normal Python REPL is used, your interactive commands will be written to and
read from this file.

Note that the ``$PYTHONSTARTUP`` environment variable will also be honored if
set, and any file named by this variable will be read at start up time.  It's
common practice to *also* enable GNU readline history in a ``$PYTHONSTARTUP``
file and if you do this, be aware that it will interact badly with
``[shell]history_file``, causing your history to be written twice.  To disable
this when using the interactive ``shell`` command, do something like::

    $ PYTHONSTARTUP= mailman shell

to temporarily unset the environment variable.


IPython
-------

You can use IPython_ as the interactive shell by setting the
``[shell]use_ipython`` variables in your `mailman.cfg` file to ``yes``.
IPython must be installed and available on your system

When using IPython, the ``[shell]history_file`` is not used.


.. Clean up
   >>> sys.path = old_path

.. _IPython: http://ipython.org/
.. _REPL: https://en.wikipedia.org/wiki/REPL
.. _`GNU readline`: https://docs.python.org/3/library/readline.html
