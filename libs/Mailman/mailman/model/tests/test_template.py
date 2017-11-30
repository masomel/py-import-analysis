# Copyright (C) 2016-2017 by the Free Software Foundation, Inc.
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

"""Test the template manager."""

import unittest
import threading

from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, HTTPServer
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.interfaces.domain import IDomainManager
from mailman.interfaces.template import ITemplateLoader, ITemplateManager
from mailman.testing.helpers import wait_for_webservice
from mailman.testing.layers import ConfigLayer
from mailman.utilities.i18n import find
from requests import HTTPError
from tempfile import TemporaryDirectory
from urllib.error import URLError
from zope.component import getUtility

# New in Python 3.5.
try:
    from http import HTTPStatus
except ImportError:
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

    def do_GET(self):
        if self.path == '/welcome_3.txt':
            if self.headers['Authorization'] != 'Basic YW5uZTppcyBzcGVjaWFs':
                self.send_error(HTTPStatus.FORBIDDEN)
                return
        response = TEXTS.get(self.path)
        if response is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-Type', 'UTF-8')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))


class HTTPLayer(ConfigLayer):
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


class TestTemplateCache(unittest.TestCase):
    layer = HTTPLayer

    def setUp(self):
        self._templatemgr = getUtility(ITemplateManager)

    def test_http_set_get(self):
        self._templatemgr.set(
            'list:user:notice:welcome', 'test.example.com',
            'http://localhost:8180/welcome_1.txt')
        contents = self._templatemgr.get(
            'list:user:notice:welcome', 'test.example.com')
        self.assertEqual(contents, WELCOME_1)

    def test_http_set_override(self):
        self._templatemgr.set(
            'list:user:notice:welcome', 'test.example.com',
            'http://localhost:8180/welcome_1.txt')
        # Resetting the template with the same context and domain, but a
        # different url overrides the previous value.
        self._templatemgr.set(
            'list:user:notice:welcome', 'test.example.com',
            'http://localhost:8180/welcome_2.txt')
        contents = self._templatemgr.get(
            'list:user:notice:welcome', 'test.example.com')
        self.assertEqual(contents, WELCOME_2)

    def test_http_get_cached(self):
        self._templatemgr.set(
            'list:user:notice:welcome', 'test.example.com',
            'http://localhost:8180/welcome_1.txt')
        # The first one warms the cache.
        self._templatemgr.get('list:user:notice:welcome', 'test.example.com')
        # The second one hits the cache.
        contents = self._templatemgr.get(
            'list:user:notice:welcome', 'test.example.com')
        self.assertEqual(contents, WELCOME_1)

    def test_http_basic_auth(self):
        # We get an HTTP error when we forget the username and password.
        self._templatemgr.set(
            'list:user:notice:welcome', 'test.example.com',
            'http://localhost:8180/welcome_3.txt')
        with self.assertRaises(HTTPError) as cm:
            self._templatemgr.get(
                'list:user:notice:welcome', 'test.example.com')
        self.assertEqual(cm.exception.response.status_code, 403)
        self.assertEqual(cm.exception.response.reason, 'Forbidden')
        # But providing the basic auth information let's it work.
        self._templatemgr.set(
            'list:user:notice:welcome', 'test.example.com',
            'http://localhost:8180/welcome_3.txt',
            username='anne', password='is special')
        contents = self._templatemgr.get(
            'list:user:notice:welcome', 'test.example.com')
        self.assertEqual(contents, WELCOME_3)

    def test_delete(self):
        self._templatemgr.set(
            'list:user:notice:welcome', 'test.example.com',
            'http://localhost:8180/welcome_1.txt')
        self._templatemgr.get('list:user:notice:welcome', 'test.example.com')
        self._templatemgr.delete(
            'list:user:notice:welcome', 'test.example.com')
        self.assertIsNone(
            self._templatemgr.get(
                'list:user:notice:welcome', 'test.example.com'))

    def test_delete_missing(self):
        self._templatemgr.delete(
            'list:user:notice:welcome', 'test.example.com')
        self.assertIsNone(
            self._templatemgr.get(
                'list:user:notice:welcome', 'test.example.com'))

    def test_get_keywords(self):
        self._templatemgr.set(
            'list:user:notice:welcome', 'test.example.com',
            'http://localhost:8180/${path}_${number}.txt')
        contents = self._templatemgr.get(
            'list:user:notice:welcome', 'test.example.com',
            path='welcome', number='1')
        self.assertEqual(contents, WELCOME_1)

    def test_get_different_keywords(self):
        self._templatemgr.set(
            'list:user:notice:welcome', 'test.example.com',
            'http://localhost:8180/${path}_${number}.txt')
        contents = self._templatemgr.get(
            'list:user:notice:welcome', 'test.example.com',
            path='welcome', number='1')
        self.assertEqual(contents, WELCOME_1)
        contents = self._templatemgr.get(
            'list:user:notice:welcome', 'test.example.com',
            path='welcome', number='2')
        self.assertEqual(contents, WELCOME_2)

    def test_not_found(self):
        # A 404 is treated specially, resulting in the empty string.
        self._templatemgr.set(
            'list:user:notice:welcome', 'test.example.com',
            'http://localhost:8180/missing.txt')
        contents = self._templatemgr.get(
            'list:user:notice:welcome', 'test.example.com')
        self.assertEqual(contents, '')


class TestTemplateLoader(unittest.TestCase):
    """Test the template downloader API."""

    layer = HTTPLayer

    def setUp(self):
        resources = ExitStack()
        self.addCleanup(resources.close)
        var_dir = resources.enter_context(TemporaryDirectory())
        config.push('template config', """\
        [paths.testing]
        var_dir: {}
        """.format(var_dir))
        resources.callback(config.pop, 'template config')
        self._mlist = create_list('test@example.com')
        self._loader = getUtility(ITemplateLoader)
        self._manager = getUtility(ITemplateManager)

    def test_domain_context(self):
        self._manager.set(
            'list:user:notice:welcome', 'example.com',
            'http://localhost:8180/$domain_name/welcome_4.txt')
        domain = getUtility(IDomainManager).get('example.com')
        content = self._loader.get('list:user:notice:welcome', domain)
        self.assertEqual(content, 'This is a domain welcome.\n')

    def test_domain_content_fallback(self):
        self._manager.set(
            'list:user:notice:welcome', 'example.com',
            'http://localhost:8180/$domain_name/welcome_4.txt')
        content = self._loader.get('list:user:notice:welcome', self._mlist)
        self.assertEqual(content, 'This is a domain welcome.\n')

    def test_site_context(self):
        self._manager.set(
            'list:user:notice:welcome', None,
            'http://localhost:8180/welcome_2.txt')
        content = self._loader.get('list:user:notice:welcome')
        self.assertEqual(content, "Sure, I guess you're welcome.\n")

    def test_site_context_mailman(self):
        self._manager.set(
            'list:user:notice:welcome', None,
            'mailman:///welcome.txt')
        template_content = self._loader.get('list:user:notice:welcome')
        path, fp = find('list:user:notice:welcome.txt')
        try:
            found_contents = fp.read()
        finally:
            fp.close()
        self.assertEqual(template_content, found_contents)

    def test_bad_context(self):
        self.assertRaises(
            ValueError, self._loader.get, 'list:user:notice:welcome', object())

    def test_no_such_file(self):
        self.assertRaises(URLError, self._loader.get, 'missing', self._mlist)

    def test_403_forbidden(self):
        # 404s are swallowed, but not 403s.
        self._manager.set(
            'forbidden', 'test.example.com',
            'http://localhost:8180/welcome_3.txt')
        self.assertRaises(URLError, self._loader.get, 'forbidden', self._mlist)


# Response texts.
WELCOME_1 = """\
Welcome to the {fqdn_listname} mailing list!
"""

WELCOME_2 = """\
Sure, I guess you're welcome.
"""

WELCOME_3 = """\
Well?  Come.
"""

WELCOME_4 = """\
This is a domain welcome.
"""

TEXTS = {
    '/welcome_1.txt': WELCOME_1,
    '/welcome_2.txt': WELCOME_2,
    '/welcome_3.txt': WELCOME_3,
    '/example.com/welcome_4.txt': WELCOME_4,
    }
