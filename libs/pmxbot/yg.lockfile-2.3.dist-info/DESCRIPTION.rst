.. image:: https://img.shields.io/pypi/v/yg.lockfile.svg
   :target: https://pypi.org/project/yg.lockfile

.. image:: https://img.shields.io/pypi/pyversions/yg.lockfile.svg

.. image:: https://img.shields.io/pypi/dm/yg.lockfile.svg

.. image:: https://img.shields.io/travis/yougov/yg.lockfile/master.svg
   :target: http://travis-ci.org/yougov/yg.lockfile

A FileLock class that implements a context manager with timeouts on top of
`zc.lockfile`, an excellent, cross-platorm implementation of file locking.

License
=======

License is indicated in the project metadata (typically one or more
of the Trove classifiers). For more details, see `this explanation
<https://github.com/jaraco/skeleton/issues/1>`_.

Usage
=====

Example usage::

    import yg.lockfile
    try:
    	with yg.lockfile.FileLock('/tmp/lockfile', timeout=900):
    		protected_operation()
    except yg.lockfile.FileLockTimeout:
    	handle_unable_to_lock()



