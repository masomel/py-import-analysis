# Copyright (C) 2014-2017 by the Free Software Foundation, Inc.
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

"""Test system configuration read-only access."""

import unittest

from mailman.testing.helpers import call_api
from mailman.testing.layers import RESTLayer
from urllib.error import HTTPError


class TestSystemConfiguration(unittest.TestCase):
    layer = RESTLayer
    maxDiff = None

    def test_basic_system_configuration(self):
        # Read some basic system configuration value, just to prove that the
        # infrastructure works.
        url = 'http://localhost:9001/3.0/system/configuration/mailman'
        json, response = call_api(url)
        # There must be an `http_etag` key, but we don't care about its value.
        self.assertIn('http_etag', json)
        del json['http_etag']
        self.assertEqual(json, dict(
            cache_life='7d',
            default_language='en',
            email_commands_max_lines='10',
            filtered_messages_are_preservable='no',
            html_to_plain_text_command='/usr/bin/lynx -dump $filename',
            layout='testing',
            listname_chars='[-_.0-9a-z]',
            noreply_address='noreply',
            pending_request_life='3d',
            post_hook='',
            pre_hook='',
            self_link='http://localhost:9001/3.0/system/configuration/mailman',
            sender_headers='from from_ reply-to sender',
            site_owner='noreply@example.com',
            ))

    def test_dmarc_system_configuration(self):
        # Test the [dmarc] section.
        url = 'http://localhost:9001/3.0/system/configuration/dmarc'
        json, response = call_api(url)
        # There must be an `http_etag` key, but we don't care about its value.
        self.assertIn('http_etag', json)
        del json['http_etag']
        self.assertEqual(json, dict(
            cache_lifetime='7d',
            org_domain_data_url=                                  # noqa: E251
                'https://publicsuffix.org/list/public_suffix_list.dat',
            resolver_lifetime='5s',
            resolver_timeout='3s',
            self_link='http://localhost:9001/3.0/system/configuration/dmarc',
            ))

    def test_dotted_section(self):
        # A dotted section works too.
        url = 'http://localhost:9001/3.0/system/configuration/language.fr'
        json, response = call_api(url)
        # There must be an `http_etag` key, but we don't care about its value.
        self.assertIn('http_etag', json)
        del json['http_etag']
        self.assertEqual(json, dict(
            description='French',
            charset='iso-8859-1',
            enabled='yes',
            self_link=('http://localhost:9001/3.0/system'
                       '/configuration/language.fr'),
            ))

    def test_multiline(self):
        # Some values contain multiple lines.  It is up to the client to split
        # on whitespace.
        url = 'http://localhost:9001/3.0/system/configuration/nntp'
        json, response = call_api(url)
        value = json['remove_headers']
        self.assertEqual(sorted(value.split()), [
            'date-received',
            'nntp-posting-date',
            'nntp-posting-host',
            'posted',
            'posting-version',
            'received',
            'relay-version',
            'x-complaints-to',
            'x-trace',
            'xref',
            ])

    def test_all_sections(self):
        # Getting the top level configuration object returns a list of all
        # existing sections.
        url = 'http://localhost:9001/3.0/system/configuration'
        json, response = call_api(url)
        self.assertIn('http_etag', json)
        self.assertEqual(sorted(json['sections']), [
            'antispam',
            'archiver.mail_archive',
            'archiver.master',
            'archiver.mhonarc',
            'archiver.prototype',
            'bounces',
            'database',
            'devmode',
            'digests',
            'dmarc',
            'language.ar',
            'language.ast',
            'language.ca',
            'language.cs',
            'language.da',
            'language.de',
            'language.el',
            'language.en',
            'language.es',
            'language.et',
            'language.eu',
            'language.fi',
            'language.fr',
            'language.gl',
            'language.he',
            'language.hr',
            'language.hu',
            'language.ia',
            'language.it',
            'language.ja',
            'language.ko',
            'language.lt',
            'language.nl',
            'language.no',
            'language.pl',
            'language.pt',
            'language.pt_BR',
            'language.ro',
            'language.ru',
            'language.sk',
            'language.sl',
            'language.sr',
            'language.sv',
            'language.tr',
            'language.uk',
            'language.vi',
            'language.zh_CN',
            'language.zh_TW',
            'logging.archiver',
            'logging.bounce',
            'logging.config',
            'logging.database',
            'logging.debug',
            'logging.error',
            'logging.fromusenet',
            'logging.http',
            'logging.locks',
            'logging.mischief',
            'logging.root',
            'logging.runner',
            'logging.smtp',
            'logging.subscribe',
            'logging.vette',
            'mailman',
            'mta',
            'nntp',
            'passwords',
            'paths.dev',
            'paths.fhs',
            'paths.here',
            'paths.local',
            'paths.testing',
            'runner.archive',
            'runner.bad',
            'runner.bounces',
            'runner.command',
            'runner.digest',
            'runner.in',
            'runner.lmtp',
            'runner.nntp',
            'runner.out',
            'runner.pipeline',
            'runner.rest',
            'runner.retry',
            'runner.shunt',
            'runner.virgin',
            'shell',
            'styles',
            'webservice',
            ])

    def test_no_such_section(self):
        # A bogus section returns a 404.
        url = 'http://localhost:9001/3.0/system/configuration/nosuchsection'
        with self.assertRaises(HTTPError) as cm:
            call_api(url)
        self.assertEqual(cm.exception.code, 404)

    def test_too_many_path_components(self):
        # More than two path components is an error, even if they name a valid
        # configuration variable.
        url = 'http://localhost:9001/3.0/system/configuration/mailman/layout'
        with self.assertRaises(HTTPError) as cm:
            call_api(url)
        self.assertEqual(cm.exception.code, 400)

    def test_read_only(self):
        # The entire configuration is read-only.
        url = 'http://localhost:9001/3.0/system/configuration'
        with self.assertRaises(HTTPError) as cm:
            call_api(url, {'foo': 'bar'})
        # 405 is Method Not Allowed.
        self.assertEqual(cm.exception.code, 405)

    def test_section_read_only(self):
        # Sections are also read-only.
        url = 'http://localhost:9001/3.0/system/configuration/mailman'
        with self.assertRaises(HTTPError) as cm:
            call_api(url, {'foo': 'bar'})
        # 405 is Method Not Allowed.
        self.assertEqual(cm.exception.code, 405)
