# Copyright (C) 2009-2017 by the Free Software Foundation, Inc.
#
# This file is part of GNU Mailman.
#
# GNU Mailman is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# GNU Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# GNU Mailman.  If not, see <http://www.gnu.org/licenses/>.

"""Doctest layer setup."""

import threading

from http.server import BaseHTTPRequestHandler, HTTPServer
from mailman.testing.helpers import wait_for_webservice
from mailman.testing.layers import RESTLayer
from public import public


# New in Python 3.5.
try:
    from http import HTTPStatus
except ImportError:                                 # pragma: no cover
    class HTTPStatus:
        FORBIDDEN = 403
        NOT_FOUND = 404
        OK = 200


# We need a web server to vend non-mailman: urls.
class TestableHandler(BaseHTTPRequestHandler):
    # Be quiet.
    def log_request(*args, **kws):
        pass

    log_error = log_request

    def do_GET(self):                             # pragma: no cover
        if self.path == '/welcome_2.txt':
            if self.headers['Authorization'] != 'Basic YW5uZTppcyBzcGVjaWFs':
                self.send_error(HTTPStatus.FORBIDDEN)
                return
        response = TEXTS.get(self.path)
        if response is None:
            self.send_error(HTTPStatus.NOT_FOUND)   # pragma: no cover
            return
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'UTF-8')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))


class HTTPLayer(RESTLayer):
    httpd = None

    @classmethod
    def setUp(cls):
        assert cls.httpd is None, 'Layer already set up'
        cls.httpd = HTTPServer(('localhost', 8180), TestableHandler)
        cls._thread = threading.Thread(target=cls.httpd.serve_forever)
        cls._thread.daemon = True
        cls._thread.start()
        wait_for_webservice('localhost', 8180)

    @classmethod
    def tearDown(cls):
        assert cls.httpd is not None, 'Layer not set up'
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls._thread.join()


public(layer=HTTPLayer)


# Response texts.
WELCOME_1 = """\
Welcome to the "$list_name" mailing list!

To post to this list, send your email to:

  $fqdn_listname

There is a Code of Conduct for this mailing list which you can view at
http://www.example.com/code-of-conduct.html
"""

WELCOME_2 = """\
I'm glad you made it!
"""

WELCOME_3 = """\
Je suis heureux que vous pouvez nous rejoindre!
"""

WELCOME_4 = """\
Welcome to the $list_name list in the $domain domain.
"""

WELCOME_5 = """\
Yay! You joined the $fqdn_listname mailing list.
"""


TEXTS = {
    '/welcome_1.txt': WELCOME_1,
    '/welcome_2.txt': WELCOME_2,
    '/ant.example.com/fr/welcome_3.txt': WELCOME_3,
    '/welcome_4.txt': WELCOME_4,
    '/welcome_5.txt': WELCOME_5,
    }
