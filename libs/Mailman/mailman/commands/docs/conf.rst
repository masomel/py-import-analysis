============================
Display configuration values
============================

Just like the `Postfix command postconf(1)`_, the ``mailman conf`` command
lets you dump one or more Mailman configuration variables to standard output
or a file.

Mailman's configuration is divided in multiple sections which contain multiple
key-value pairs.  The ``mailman conf`` command allows you to display a
specific key-value pair, or several key-value pairs.

    >>> class FakeArgs:
    ...     key = None
    ...     section = None
    ...     output = None
    >>> from mailman.commands.cli_conf import Conf
    >>> command = Conf()

To get a list of all key-value pairs of any section, you need to call the
command without any options.

    >>> command.process(FakeArgs)
    [antispam] header_checks:
    ...
    [logging.bounce] level: info
    ...
    [mailman] site_owner: noreply@example.com
    ...

You can list all the key-value pairs of a specific section.

    >>> FakeArgs.section = 'shell'
    >>> command.process(FakeArgs)
    [shell] banner: Welcome to the GNU Mailman shell
    [shell] history_file:
    [shell] prompt: >>>
    [shell] use_ipython: no

You can also pass a key and display all key-value pairs matching the given
key, along with the names of the corresponding sections.

    >>> FakeArgs.section = None
    >>> FakeArgs.key = 'path'
    >>> command.process(FakeArgs)
    [logging.archiver] path: mailman.log
    [logging.bounce] path: bounce.log
    [logging.config] path: mailman.log
    [logging.database] path: mailman.log
    [logging.debug] path: debug.log
    [logging.error] path: mailman.log
    [logging.fromusenet] path: mailman.log
    [logging.http] path: mailman.log
    [logging.locks] path: mailman.log
    [logging.mischief] path: mailman.log
    [logging.root] path: mailman.log
    [logging.runner] path: mailman.log
    [logging.smtp] path: smtp.log
    [logging.subscribe] path: mailman.log
    [logging.vette] path: mailman.log

If you specify both a section and a key, you will get the corresponding value.

    >>> FakeArgs.section = 'mailman'
    >>> FakeArgs.key = 'site_owner'
    >>> command.process(FakeArgs)
    noreply@example.com


.. _`Postfix command postconf(1)`: http://www.postfix.org/postconf.1.html
