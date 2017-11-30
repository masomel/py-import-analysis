==========================
 Setting up your database
==========================

Mailman uses the SQLAlchemy_ ORM to provide persistence of data in a
relational database.  By default, Mailman uses Python's built-in SQLite3_
database, however, SQLAlchemy is compatible with PostgreSQL_ and MySQL_, among
possibly others.

Currently, Mailman is known to work with the SQLite3, PostgreSQL, and MySQL
databases.  (Volunteers to port it to other databases are welcome!).  If you
want to use SQLite3, you generally don't need to change anything, but if you
want Mailman to use PostgreSQL or MySQL, you'll need to set those up first,
and then change a configuration variable in your ``/etc/mailman.cfg`` file.

Two configuration variables control which database Mailman uses.  The first
names the class implementing the database interface.  The second names the URL
for connecting to the database.  Both variables live in the ``[database]``
section of the configuration file.


SQLite3
=======

As mentioned, if you want to use SQLite3 in the default configuration, you
generally don't need to change anything.  However, if you want to change where
the SQLite3 database is stored, you can change the ``url`` variable in the
``[database]`` section.  By default, the database is stored in the *data
directory* in the ``mailman.db`` file.  Here's how to tell Mailman to store
its database in ``/var/lib/mailman/sqlite.db`` file::

    [database]
    url: sqlite:////var/lib/mailman/sqlite.db


PostgreSQL
==========

First, you need to configure PostgreSQL itself.  This `Ubuntu article`_ may
help.  Let's say you create the `mailman` database in PostgreSQL via::

    $ sudo -u postgres createdb -O $USER mailman

You would also need the Python driver `psycopg2` for PostgreSQL::

    $ pip install psycopg2

You would then need to set both the `class` and `url` variables in
`mailman.cfg` like so::

    [database]
    class: mailman.database.postgresql.PostgreSQLDatabase
    url: postgres://myuser:mypassword@mypghost/mailman

If you have any problems, you may need to delete the database and re-create
it::

    $ sudo -u postgres dropdb mailman
    $ sudo -u postgres createdb -O myuser mailman

Many thanks to Stephen A. Goss for his contribution of PostgreSQL support.


MySQL
=====

First you need to configure MySQL itself.  Lets say you create the `mailman`
database in MySQL via::

    mysql> CREATE DATABASE mailman;

You would also need the Python driver `pymysql` for MySQL.::

    $ pip install pymysql

You would then need to set both the `class` and `url` variables in
`mailman.cfg` like so::

    [database]
    class: mailman.database.mysql.MySQLDatabase
    url: mysql+pymysql://myuser:mypassword@mymysqlhost/mailman?charset=utf8&use_unicode=1

The last part of the url specifies the charset that client expects from the
server and to use Unicode via the flag `use_unicode`.  You can find more about
these options on the `SQLAlchemy's MySQL page`_.

If you have any problems, you may need to delete the database and re-create
it::

    mysql> DROP DATABASE mailman;
    mysql> CREATE DATABASE mailman;


Database Migrations
===================

Mailman uses `Alembic`_ to manage database migrations.  Let's say you change
something in the models, what steps are needed to reflect that change in the
database schema?  You need to create and enter a virtual environment, install
Mailman into that, and then run the ``alembic`` command.  For example::

    $ python3 -m venv /tmp/mm3
    $ source /tmp/mm3/bin/activate
    $ python setup.py develop
    $ mailman info
    $ alembic -c src/mailman/config/alembic.cfg revision --autogenerate -m
      "<migration_name>"
    $ deactivate

This would create a new migration which would be applied to the database
automatically on the next run of Mailman.

People upgrading Mailman from previous versions need not do anything manually,
as soon as a new migration is added in the sources, it will be automatically
reflected in the schema on first-run post-update.

**Note:** When auto-generating migrations using Alembic, be sure to check
the created migration before adding it to the version control.  You will have
to manually change some of the special data types defined in
``mailman.database.types``.  For example, ``mailman.database.types.Enum()``
needs to be changed to ``sa.Integer()``, as the ``Enum`` type stores just the
integer in the database.  A more complex migration would be needed for
``UUID`` depending upon the database layer to be used.


.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _SQLite3: http://docs.python.org/library/sqlite3.html
.. _PostgreSQL: http://www.postgresql.org/
.. _MySQL: http://dev.mysql.com/
.. _`Ubuntu article`: https://help.ubuntu.com/community/PostgreSQL
.. _`Alembic`: https://alembic.readthedocs.org/en/latest/
.. _`SQLAlchemy's MySQL page`: http://docs.sqlalchemy.org/en/latest/dialects/mysql.html#unicode
