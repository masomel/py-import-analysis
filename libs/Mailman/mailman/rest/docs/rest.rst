.. _rest-api:

========================================
 Mailman 3 Core administrative REST API
========================================

Here is extensive documentation on the Mailman Core administrative REST API.


The REST server
===============

Mailman exposes a REST HTTP server for administrative control.

The server listens for connections on a configurable host name and port.

It is always protected by HTTP basic authentication using a single global
user name and password. The credentials are set in the `[webservice]` section
of the configuration using the `admin_user` and `admin_pass` properties.

Because the REST server has full administrative access, it should never be
exposed to the public internet.  By default it only listens to connections on
``localhost``.  Don't change this unless you really know what you're doing.
In addition you should set the user name and password to secure values and
distribute them to any REST clients with reasonable precautions.

The Mailman major and minor version numbers are in the URL.

You can write your own HTTP clients to speak this API, or you can use the
`official Python bindings`_.


.. toctree::
   :glob:
   :maxdepth: 1

   ./basic
   ./collections
   ./helpers
   ./systemconf
   ./domains
   ./lists
   ./listconf
   ./addresses
   ./users
   ./membership
   ./queues
   ./*


.. _`official Python bindings`: https://mailmanclient.readthedocs.io/en/latest/
