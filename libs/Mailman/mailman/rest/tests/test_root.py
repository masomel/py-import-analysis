# Copyright (C) 2011-2017 by the Free Software Foundation, Inc.
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

"""REST root object tests."""

import os
import requests
import unittest

from mailman.config import config
from mailman.core.system import system
from mailman.database.transaction import transaction
from mailman.interfaces.template import ITemplateManager
from mailman.testing.helpers import call_api
from mailman.testing.layers import RESTLayer
from urllib.error import HTTPError
from zope.component import getUtility


class TestRoot(unittest.TestCase):
    layer = RESTLayer

    def test_root_system_backward_compatibility(self):
        # The deprecated path for getting system version information points
        # you to the new URL.
        url = 'http://localhost:9001/3.0/system'
        new = '{}/versions'.format(url)
        json, response = call_api(url)
        self.assertEqual(json['mailman_version'], system.mailman_version)
        self.assertEqual(json['python_version'], system.python_version)
        self.assertEqual(json['self_link'], new)

    def test_system_versions(self):
        # System version information is available via REST.
        url = 'http://localhost:9001/3.0/system/versions'
        json, response = call_api(url)
        self.assertEqual(json['mailman_version'], system.mailman_version)
        self.assertEqual(json['python_version'], system.python_version)
        self.assertEqual(json['self_link'], url)

    def test_path_under_root_does_not_exist(self):
        # Accessing a non-existent path under root returns a 404.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/does-not-exist')
        self.assertEqual(cm.exception.code, 404)

    def test_system_url_not_preferences(self):
        # /system/foo where `foo` is not `preferences`.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/system/foo')
        self.assertEqual(cm.exception.code, 404)

    def test_system_preferences_are_read_only(self):
        # /system/preferences are read-only.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/system/preferences', {
                     'acknowledge_posts': True,
                     }, method='PATCH')
        self.assertEqual(cm.exception.code, 405)
        # /system/preferences are read-only.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/system/preferences', {
                'acknowledge_posts': False,
                'delivery_mode': 'regular',
                'delivery_status': 'enabled',
                'hide_address': True,
                'preferred_language': 'en',
                'receive_list_copy': True,
                'receive_own_postings': True,
                }, method='PUT')
        self.assertEqual(cm.exception.code, 405)

    def test_queue_directory(self):
        # The REST runner is not queue runner, so it should not have a
        # directory in var/queue.
        queue_directory = os.path.join(config.QUEUE_DIR, 'rest')
        self.assertFalse(os.path.isdir(queue_directory))

    def test_no_basic_auth(self):
        # If Basic Auth credentials are missing, it is a 401 error.
        response = requests.get('http://localhost:9001/3.0/system')
        self.assertEqual(response.status_code, 401)
        json = response.json()
        self.assertEqual(json['title'], '401 Unauthorized')
        self.assertEqual(json['description'], 'REST API authorization failed')

    def test_unauthorized(self):
        # Bad Basic Auth credentials results in a 401 error.
        response = requests.get(
            'http://localhost:9001/3.0/system',
            auth=('baduser', 'badpass'))
        self.assertEqual(response.status_code, 401)
        json = response.json()
        self.assertEqual(json['title'], '401 Unauthorized')
        self.assertEqual(json['description'], 'REST API authorization failed')

    def test_reserved_bad_subpath(self):
        # Only <api>/reserved/uids/orphans is a defined resource.  DELETEing
        # anything else gives a 404.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/reserved/uids/assigned',
                     method='DELETE')
        self.assertEqual(cm.exception.code, 404)

    def test_system_pipelines_are_exposed(self):
        json, response = call_api('http://localhost:9001/3.0/system/pipelines')
        self.assertEqual(json['pipelines'], sorted(config.pipelines))

    def test_system_pipelines_bad_request(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/system/pipelines/bogus')
        self.assertEqual(cm.exception.code, 400)

    def test_system_pipelines_are_read_only(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/system/pipelines', {
                'pipelines': ['pipeline_1', 'pipeline_2']
                }, method='PATCH')
        self.assertEqual(cm.exception.code, 405)
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/system/pipelines', {
                'pipelines': ['pipeline_1', 'pipeline_2']
                }, method='PUT')
        self.assertEqual(cm.exception.code, 405)

    def test_system_chains_are_exposed(self):
        json, response = call_api('http://localhost:9001/3.0/system/chains')
        self.assertEqual(json['chains'], sorted(config.chains))

    def test_system_chains_bad_request(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/system/chains/bogus')
        self.assertEqual(cm.exception.code, 400)

    def test_system_chains_are_read_only(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/system/chains', {
                'chains': ['chain_1', 'chain_2']
                }, method='PATCH')
        self.assertEqual(cm.exception.code, 405)
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/system/chains', {
                'chains': ['chain_1', 'chain_2']
                }, method='PUT')
        self.assertEqual(cm.exception.code, 405)


class TestSiteTemplates(unittest.TestCase):
    """Test /uris"""

    layer = RESTLayer

    def test_no_templates_for_api_30(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/uris')
        self.assertEqual(cm.exception.code, 404)

    def test_path_too_long(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.1/uris/foo/bar')
        self.assertEqual(cm.exception.code, 400)

    def test_get_unknown_uri(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.1/uris/not:a:template')
        self.assertEqual(cm.exception.code, 404)

    def test_get_all_uris(self):
        manager = getUtility(ITemplateManager)
        with transaction():
            manager.set(
                'list:user:notice:welcome', None,
                'http://example.com/welcome')
            manager.set(
                'list:user:notice:goodbye', None,
                'http://example.com/goodbye',
                'a user', 'the password',
                )
        json, response = call_api(
            'http://localhost:9001/3.1/uris')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['start'], 0)
        self.assertEqual(json['total_size'], 2)
        self.assertEqual(
            json['self_link'],
            'http://localhost:9001/3.1/uris')
        self.assertEqual(json['entries'], [
            {'http_etag': '"063fd6635a6035a4b7e939a304fcbd16571aa662"',
             'name': 'list:user:notice:goodbye',
             'password': 'the password',
             'self_link': ('http://localhost:9001/3.1'
                           '/uris/list:user:notice:goodbye'),
             'uri': 'http://example.com/goodbye',
             'username': 'a user',
             },
            {'http_etag': '"5c4ec63b2a0a50f96483ec85b94b80ee092af792"',
             'name': 'list:user:notice:welcome',
             'self_link': ('http://localhost:9001/3.1'
                           '/uris/list:user:notice:welcome'),
             'uri': 'http://example.com/welcome',
             }])

    def test_patch_uris(self):
        json, response = call_api(
            'http://localhost:9001/3.1/uris', {
                'list:user:notice:welcome': 'http://example.org/welcome',
                'list:user:notice:goodbye': 'http://example.org/goodbye',
                }, method='PATCH')
        self.assertEqual(response.status_code, 204)
        manager = getUtility(ITemplateManager)
        template = manager.raw('list:user:notice:welcome', None)
        self.assertEqual(template.uri, 'http://example.org/welcome')
        self.assertIsNone(template.username)
        self.assertEqual(template.password, '')
        template = manager.raw('list:user:notice:goodbye', None)
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertIsNone(template.username)
        self.assertEqual(template.password, '')

    def test_patch_uris_with_credentials(self):
        json, response = call_api(
            'http://localhost:9001/3.1/uris', {
                'list:user:notice:welcome': 'http://example.org/welcome',
                'list:user:notice:goodbye': 'http://example.org/goodbye',
                'password': 'some password',
                'username': 'anne.person',
                }, method='PATCH')
        self.assertEqual(response.status_code, 204)
        manager = getUtility(ITemplateManager)
        template = manager.raw('list:user:notice:welcome', None)
        self.assertEqual(template.uri, 'http://example.org/welcome')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:user:notice:goodbye', None)
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')

    def test_patch_uris_with_partial_credentials(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/uris', {
                    'list:user:notice:welcome': 'http://example.org/welcome',
                    'list:user:notice:goodbye': 'http://example.org/goodbye',
                    'username': 'anne.person',
                    }, method='PATCH')
        self.assertEqual(cm.exception.code, 400)

    def test_put_all_uris(self):
        json, response = call_api(
            'http://localhost:9001/3.1/uris', {
                'domain:admin:notice:new-list': '',
                'list:admin:action:post': '',
                'list:admin:action:subscribe': '',
                'list:admin:action:unsubscribe': '',
                'list:admin:notice:subscribe': '',
                'list:admin:notice:unrecognized': '',
                'list:admin:notice:unsubscribe': '',
                'list:member:digest:footer': '',
                'list:member:digest:header': '',
                'list:member:digest:masthead': '',
                'list:member:regular:footer': 'http://example.org/footer',
                'list:member:regular:header': 'http://example.org/header',
                'list:user:action:subscribe': '',
                'list:user:action:unsubscribe': '',
                'list:user:notice:goodbye': 'http://example.org/goodbye',
                'list:user:notice:hold': '',
                'list:user:notice:no-more-today': '',
                'list:user:notice:post': '',
                'list:user:notice:probe': '',
                'list:user:notice:refuse': '',
                'list:user:notice:welcome': 'http://example.org/welcome',
                'password': 'some password',
                'username': 'anne.person',
                }, method='PUT')
        self.assertEqual(response.status_code, 204)
        manager = getUtility(ITemplateManager)
        template = manager.raw('list:member:digest:footer', None)
        self.assertIsNone(template)
        template = manager.raw('list:member:digest:header', None)
        self.assertIsNone(template)
        template = manager.raw('list:member:regular:footer', None)
        self.assertEqual(template.uri, 'http://example.org/footer')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:member:regular:header', None)
        self.assertEqual(template.uri, 'http://example.org/header')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:user:notice:goodbye', None)
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:user:notice:goodbye', None)
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')

    def test_delete_all_uris(self):
        manager = getUtility(ITemplateManager)
        with transaction():
            manager.set(
                'list:user:notice:welcome', None,
                'http://example.com/welcome')
            manager.set(
                'list:user:notice:goodbye', None,
                'http://example.com/goodbye',
                'a user', 'the password',
                )
        json, response = call_api(
            'http://localhost:9001/3.1/uris',
            method='DELETE')
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(manager.raw('list:user:notice:welcome', None))
        self.assertIsNone(manager.raw('list:user:notice:goodbye', None))

    def test_get_a_url(self):
        with transaction():
            getUtility(ITemplateManager).set(
                'list:user:notice:welcome', None,
                'http://example.com/welcome')
        json, response = call_api(
            'http://localhost:9001/3.1/uris/list:user:notice:welcome')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json, {
            'http_etag': '"86e360d83197561d50826ad6d15e9c30923b82d6"',
            'self_link': ('http://localhost:9001/3.1'
                          '/uris/list:user:notice:welcome'),
            'uri': 'http://example.com/welcome',
            })

    def test_get_a_bad_url(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/uris/list:user:notice:notemplate')
        self.assertEqual(cm.exception.code, 404)

    def test_get_unset_url(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/uris/list:user:notice:welcome')
        self.assertEqual(cm.exception.code, 404)

    def test_patch_url_with_too_many_parameters(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/uris', {
                    'list:user:notice:welcome': 'http://example.org/welcome',
                    'list:user:notice:goodbye': 'http://example.org/goodbye',
                    'secret': 'some password',
                    'person': 'anne.person',
                    }, method='PATCH')
        self.assertEqual(cm.exception.code, 400)
