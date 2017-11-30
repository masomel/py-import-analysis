.. _configuration:

=====================
 Configuring Mailman
=====================

Mailman is configured via an "ini"-style configuration file, usually called
``mailman.cfg``.  Most of the defaults produce a usable system, but you will
almost certainly have to set up a few things before you run Mailman for the
first time.  You only need to include those settings which you want to change;
everything else is inherited.

These file system paths are searched in the following order to find your
site's custom ``mailman.cfg`` file.  The first file found is used.

* The file system path specified by the environment variable
  ``$MAILMAN_CONFIG_FILE``
* ``mailman.cfg`` in the current working directory
* ``var/etc/mailman.cfg`` relative to the current working directory
* ``$HOME/.mailman.cfg``
* ``/etc/mailman.cfg``
* ``../../etc/mailman.cfg`` relative to the working directory of ``argv[0]``

You can also use the ``-C`` option to specify an explicit path, and this
always takes precedence.  See ``mailman --help`` for more details.

You **must** restart Mailman for any changes to take effect.


Which configuration file is in use?
===================================

Mailman itself will tell you which configuration file is being used when you
run the ``mailman info`` command::

    $ mailman info
    GNU Mailman 3.1.0b4 (Between The Wheels)
    Python 3.5.3 (default, Jan 19 2017, 14:11:04)
    [GCC 6.3.0 20170118]
    config file: /home/mailman/var/etc/mailman.cfg
    db url: sqlite:////home/mailman/var/data/mailman.db
    devmode: DISABLED
    REST root url: http://localhost:8001/3.1/
    REST credentials: restadmin:restpass

The first time you run this command it will create the configuration file and
directory using the built-in defaults, so use ``-C`` to specify an alternative
location.  Of course the ``info`` subcommand shows you other interesting
things about your Mailman instance.


Schemas, templates, and master sections
=======================================

Mailman's configuration system is built on top of `lazr.config
<http://pythonhosted.org/lazr.config/>`_ although in general the details
aren't important.  Basically there is a ``schema.cfg`` file included in the
source tree, which defines all the available sections and variables, along
with global defaults.  There is a built-in base ``mailman.cfg`` file also
included in the source tree, which further refines the defaults.

Your custom ``mailman.cfg`` file, found using the search locations described
above, provides the final override for these settings.

The ``schema.cfg`` file describes every section, variable, and permissible
values, so you should consult this for more details.  The ``schema.cfg`` file
is included verbatim below.

You will notice two types of special sections in the ``schema.cfg`` files;
those that end with the ``.template`` suffix, and others which end in a
``.master`` suffix.  There are no other special sections.

Templates provide exactly that: a template for other similarly named
sections.  So for example, you will see a section labeled ``logging.template``
which provides some configuration variables and some basic defaults.  You will
also see a section called ``logging.bounce`` which refines the
``logging.template`` section by overriding one or more settings.

If you wanted to change the default logging level for the database component
in Mailman, say from ``warn`` to ``info``, you would add this to your
``mailman.cfg`` file::

    [logging.database]
    level: info

Generally you won't add new template specialization sections; everything you
need is already defined.

You will also see sections labeled with the ``.master`` suffix.  For the most
part you can treat these exactly the same as ``.template`` sections; the
differences are only relevant for Mailman developers [#]_.  An example of a
``.master`` section is ``[runner.master]`` which is used to define the
defaults for all the :ref:`runner processes <runners>`.  This is specialized
in the built-in ``mailman.cfg`` file, where you'll see sections like
``[runner.archive]`` and ``[runner.in]``.  You won't need to specially the
master section yourself, but instead you can override some settings in the
individual runner sections.


How do I change a setting?
==========================

If you think you want to change something, it can be a little tricky to find
exactly the setting you'll need.  The first step is to use the ``mailman
conf`` command to print all the current variables and their values.  With no
options, this will print all the hundreds of (sorted!) available settings to
standard output.  You can narrow this down in two ways.  You can print just
the values of a particular section::

    $ mailman conf -s webservice
    [webservice] admin_pass: restpass
    [webservice] admin_user: restadmin
    [webservice] api_version: 3.1
    [webservice] hostname: localhost
    [webservice] port: 8001
    [webservice] show_tracebacks: yes
    [webservice] use_https: no

Let's say you wanted to change the port the REST API listens on.  Just add
this to your ``mailman.cfg`` file::

    [webservice]
    port: 8080

You can also search for a specific setting::

    $ mailman conf -k prompt
    [shell] prompt: >>>

The ``mailman conf`` command does not provide documentation about sections or
variables.  In order to get more information about what a particular variable
controls, read the ``schema.cfg`` and built-in base ``mailman.cfg`` file.


schema.cfg
==========

``schema.cfg`` defines the ini-file schema and contains documentation for
every section and configuration variable.

.. literalinclude:: ../schema.cfg


mailman.cfg
===========

Configuration settings provided in the built-in base ``mailman.cfg`` file
overrides those provided in ``schema.cfg``.

.. literalinclude:: ../mailman.cfg


.. [#] The technical differences are described in the `lazr.config
       <http://pythonhosted.org/lazr.config/>`_ package, upon which Mailman's
       configuration system is based.
