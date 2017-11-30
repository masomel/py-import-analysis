******
finder
******

|version| |travis| |coveralls| |license|

Command line interface for searching a given pattern in the given directory/file paths.

Links
=====

 - Project: https://github.com/bharadwajyarlagadda/finder
 - Documentation: Wiki_
 - Pypi: https://pypi.python.org/pypi/finder
 - TravisCI: https://travis-ci.org/bharadwajyarlagadda/finder

Quickstart
==========

Install using pip:

::

    pip install finder


Features
========

- Supported on Python 3.3+.


.. |version| image:: https://img.shields.io/pypi/v/finder.svg?style=flat-square
    :target: https://pypi.python.org/pypi/finder/

.. |travis| image:: https://img.shields.io/travis/bharadwajyarlagadda/finder/master.svg?style=flat-square
    :target: https://travis-ci.org/bharadwajyarlagadda/finder

.. |coveralls| image:: https://img.shields.io/coveralls/bharadwajyarlagadda/finder/master.svg?style=flat-square
    :target: https://coveralls.io/r/bharadwajyarlagadda/finder

.. |license| image:: https://img.shields.io/pypi/l/finder.svg?style=flat-square
    :target: https://github.com/bharadwajyarlagadda/finder/blob/master/LICENSE.rst


.. _Wiki: https://github.com/bharadwajyarlagadda/finder/wiki

Changelog
=========


v1.0.2 (2017-05-07)
-------------------

- FIX bug in CHANGELOG.


v1.0.1 (2017-05-07)
-------------------

- Minor updates.


v1.0.0 (2017-05-07)
-------------------

- Add ``search`` method to search for a given pattern in the text provided.
- Add ``iterfiles`` method to yield all the file paths in a given folder path.
- Add ``is_executable`` method to validate whether the given file is a executable or not.
- Add ``read`` method to read a given file line by line.
- Add wrapper method ``find`` to iterate through the given list of files/directories and find the given pattern in the files.
- Add ``FileReader`` class to searching all the files concurrently.
- Add schemas for serializing the data to a JSON-encoded string.
- Add command line wrapper around the API. User can now use the command line interface to get all the search results.


