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

"""Test the protocol support.

For convenience, we currently don't test the http: and https: schemes here.
These are tested fairly well in the template cache tests.  We probably
eventually want to refactor that for test isolation.
"""


import os
import unittest

from contextlib import ExitStack
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.testing.layers import ConfigLayer
from mailman.utilities import protocols
from tempfile import TemporaryDirectory
from urllib.error import URLError


class TestProtocols(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        resources = ExitStack()
        self.addCleanup(resources.close)
        self.var_dir = resources.enter_context(TemporaryDirectory())
        config.push('template config', """\
        [paths.testing]
        var_dir: {}
        """.format(self.var_dir))
        resources.callback(config.pop, 'template config')
        # Put a demo template in the site directory.
        path = os.path.join(self.var_dir, 'templates', 'site', 'en')
        os.makedirs(path)
        with open(os.path.join(path, 'demo.txt'), 'w') as fp:
            print('Test content', end='', file=fp)
        self._mlist = create_list('test@example.com')

    def test_file(self):
        with TemporaryDirectory() as tempdir:
            path = os.path.join(tempdir, 'my-file')
            with open(path, 'w', encoding='utf-8') as fp:
                print('Some contents', end='', file=fp)
            contents = protocols.get('file:///{}'.format(path))
            self.assertEqual(contents, 'Some contents')

    def test_file_binary(self):
        with TemporaryDirectory() as tempdir:
            path = os.path.join(tempdir, 'my-file')
            with open(path, 'wb') as fp:
                fp.write(b'xxx')
            contents = protocols.get('file:///{}'.format(path), mode='rb')
            self.assertEqual(contents, b'xxx')

    def test_file_ascii(self):
        with TemporaryDirectory() as tempdir:
            path = os.path.join(tempdir, 'my-file')
            with open(path, 'w', encoding='us-ascii') as fp:
                print('Some contents', end='', file=fp)
            contents = protocols.get('file:///{}'.format(path),
                                     encoding='us-ascii')
            self.assertEqual(contents, 'Some contents')

    def test_mailman_internal_uris(self):
        # mailman://demo.txt
        content = protocols.get('mailman:///demo.txt')
        self.assertEqual(content, 'Test content')

    def test_mailman_internal_uris_twice(self):
        # mailman:///demo.txt
        content = protocols.get('mailman:///demo.txt')
        self.assertEqual(content, 'Test content')
        content = protocols.get('mailman:///demo.txt')
        self.assertEqual(content, 'Test content')

    def test_mailman_uri_with_language(self):
        content = protocols.get('mailman:///en/demo.txt')
        self.assertEqual(content, 'Test content')

    def test_mailman_uri_with_english_fallback(self):
        content = protocols.get('mailman:///it/demo.txt')
        self.assertEqual(content, 'Test content')

    def test_mailman_uri_with_list_name(self):
        content = protocols.get('mailman:///test@example.com/demo.txt')
        self.assertEqual(content, 'Test content')

    def test_mailman_full_uri(self):
        content = protocols.get('mailman:///test@example.com/en/demo.txt')
        self.assertEqual(content, 'Test content')

    def test_mailman_full_uri_with_english_fallback(self):
        content = protocols.get('mailman:///test@example.com/it/demo.txt')
        self.assertEqual(content, 'Test content')

    def test_uri_not_found(self):
        with self.assertRaises(URLError) as cm:
            protocols.get('mailman:///missing.txt')
        self.assertEqual(cm.exception.reason, 'No such file')

    def test_shorter_url_error(self):
        with self.assertRaises(URLError) as cm:
            protocols.get('mailman:///')
        self.assertEqual(cm.exception.reason, 'No template specified')

    def test_short_url_error(self):
        with self.assertRaises(URLError) as cm:
            protocols.get('mailman://')
        self.assertEqual(cm.exception.reason, 'No template specified')

    def test_bad_language(self):
        with self.assertRaises(URLError) as cm:
            protocols.get('mailman:///xx/demo.txt')
        self.assertEqual(cm.exception.reason, 'Bad language or list name')

    def test_bad_mailing_list(self):
        with self.assertRaises(URLError) as cm:
            protocols.get('mailman:///missing@example.com/demo.txt')
        self.assertEqual(cm.exception.reason, 'Bad language or list name')

    def test_missing_mailing_list(self):
        with self.assertRaises(URLError) as cm:
            protocols.get('mailman:///missing@example.com/it/demo.txt')
        self.assertEqual(cm.exception.reason, 'Missing list')

    def test_no_such_language(self):
        with self.assertRaises(URLError) as cm:
            protocols.get('mailman:///test@example.com/xx/demo.txt')
        self.assertEqual(cm.exception.reason, 'No such language')

    def test_too_many_path_components(self):
        with self.assertRaises(URLError) as cm:
            protocols.get('mailman:///missing@example.com/en/foo/demo.txt')
        self.assertEqual(cm.exception.reason, 'No such file')

    def test_non_ascii(self):
        # mailman://demo.txt with non-ascii content.
        test_text = b'\xe4\xb8\xad'
        path = os.path.join(self.var_dir, 'templates', 'site', 'it')
        os.makedirs(path)
        with open(os.path.join(path, 'demo.txt'), 'wb') as fp:
            fp.write(test_text)
        content = protocols.get('mailman:///it/demo.txt')
        self.assertIsInstance(content, str)
        self.assertEqual(content, test_text.decode('utf-8'))

    def test_bad_file_keyword(self):
        self.assertRaises(ValueError, protocols.get, 'file:///etc/passwd',
                          invalid_keyword='yes')

    def test_bad_mailman_keyword(self):
        self.assertRaises(ValueError, protocols.get, 'mailman:///demo.text',
                          invalid_keyword='yes')

    def test_bad_protocol(self):
        self.assertRaises(URLError, protocols.get, 'unknown:///demo.text')
