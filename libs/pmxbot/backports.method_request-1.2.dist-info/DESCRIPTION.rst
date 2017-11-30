.. image:: https://img.shields.io/pypi/v/backports.method_request.svg
   :target: https://pypi.org/project/backports.method_request

.. image:: https://img.shields.io/pypi/pyversions/backports.method_request.svg

.. image:: https://img.shields.io/pypi/dm/backports.method_request.svg

.. image:: https://img.shields.io/travis/jaraco/backports.method_request/master.svg
   :target: http://travis-ci.org/jaraco/backports.method_request

A backport of the urllib.request.MethodRequest class from Python 3.4 which
allows overriding of the method in a class attribute or as a keyword
parameter to the initializer.

See `Python 18978 <http://bugs.python.org/issue18978>`_ for details.

Works on Python 2.6 and later.


License
=======

License is indicated in the project metadata (typically one or more
of the Trove classifiers). For more details, see `this explanation
<https://github.com/jaraco/skeleton/issues/1>`_.

Usage
-----

Use ``method_request.Request`` in place of ``urllib.request.Request``::

    from backports.method_request import Request

    req = Request(..., method='PATCH')
    resp = urllib.request.urlopen(req)
    ...


