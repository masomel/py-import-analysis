======================================================
flufl.i18n - A high level API for internationalization
======================================================

This package provides a high level, convenient API for managing
internationalization translation contexts in Python application.  There is a
simple API for single-context applications, such as command line scripts which
only need to translate into one language during the entire course of their
execution.  There is a more flexible, but still convenient API for
multi-context applications, such as servers, which may need to switch language
contexts for different tasks.


Requirements
============

``flufl.i18n`` requires Python 2.7 or newer, and is compatible with Python 3.


Documentation
=============

A `simple guide`_ to using the library is available within this package, in
the form of doctests.


Project details
===============

 * Project home: https://gitlab.com/warsaw/flufl.i18n
 * Report bugs at: https://gitlab.com/warsaw/flufl.i18n/issues
 * Code hosting: https://gitlab.com/warsaw/flufl.i18n.git
 * Documentation: http://flufli18n.readthedocs.org/

You can install it with `pip`::

    % pip install flufl.i18n

You can grab the latest development copy of the code using git.  The master
repository is hosted on GitLab.  If you have git installed, you can grab
your own branch of the code like this::

    $ git clone https://gitlab.com/warsaw/flufl.i18n.git

You may contact the author via barry@python.org.


Copyright
=========

Copyright (C) 2004-2017 Barry A. Warsaw

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Table of Contents
=================

.. toctree::
    :glob:

    docs/using
    docs/*
    NEWS

.. _`simple guide`: docs/using.html
