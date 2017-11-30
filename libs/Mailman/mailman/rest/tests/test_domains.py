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

"""REST domain tests."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.database.transaction import transaction
from mailman.interfaces.domain import IDomainManager
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.template import ITemplateManager
from mailman.testing.helpers import call_api
from mailman.testing.layers import RESTLayer
from urllib.error import HTTPError
from zope.component import getUtility


class TestDomains(unittest.TestCase):
    layer = RESTLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('test@example.com')

    def test_create_domains(self):
        # Create a domain with owners.
        data = dict(
            mail_host='example.org',
            description='Example domain',
            owner=['someone@example.com', 'secondowner@example.com'],
            )
        content, response = call_api(
            'http://localhost:9001/3.0/domains', data, method="POST")
        self.assertEqual(response.status_code, 201)

    def test_patch_domain_description(self):
        # Patch the example.com description.
        data = {'description': 'Patched example domain'}
        content, response = call_api(
            'http://localhost:9001/3.0/domains/example.com',
            data,
            method='PATCH')
        self.assertEqual(response.status_code, 204)
        # Check the result.
        domain = getUtility(IDomainManager).get('example.com')
        self.assertEqual(domain.description, 'Patched example domain')

    def test_patch_domain_owner(self):
        # Patch the example.com owner.
        data = {'owner': 'anne@example.com'}
        content, response = call_api(
            'http://localhost:9001/3.0/domains/example.com',
            data,
            method='PATCH')
        self.assertEqual(response.status_code, 204)
        # Check the result.
        domain = getUtility(IDomainManager).get('example.com')
        self.assertEqual(
            [list(owner.addresses)[0].email for owner in domain.owners],
            ['anne@example.com'])

    def test_patch_domain_two_owners(self):
        # Patch the example.com owner.
        data = {'owner': ['anne@example.com', 'other@example.net']}
        content, response = call_api(
            'http://localhost:9001/3.0/domains/example.com',
            data,
            method='PATCH')
        self.assertEqual(response.status_code, 204)
        # Check the result.
        domain = getUtility(IDomainManager).get('example.com')
        self.assertEqual(
            [list(owner.addresses)[0].email for owner in domain.owners],
            ['anne@example.com', 'other@example.net'])

    def test_patch_domain_readonly(self):
        # Attempt to patch mail_host.
        data = {'mail_host': 'example.net'}
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/domains/example.com',
                data,
                method='PATCH')
        self.assertEqual(cm.exception.code, 400)

    def test_domain_create_with_single_owner(self):
        # Creating domain with single owner should not raise InvalidEmailError.
        content, response = call_api(
            'http://localhost:9001/3.0/domains', dict(
                mail_host='example.net',
                owner='anne@example.com',
                ),
            method='POST')
        self.assertEqual(response.status_code, 201)
        # The domain has the expected owner.
        domain = getUtility(IDomainManager).get('example.net')
        self.assertEqual(
            [list(owner.addresses)[0].email for owner in domain.owners],
            ['anne@example.com'])

    def test_bogus_endpoint_extension(self):
        # /domains/<domain>/lists/<anything> is not a valid endpoint.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/example.com'
                     '/lists/wrong')
        self.assertEqual(cm.exception.code, 400)

    def test_bogus_endpoint(self):
        # /domains/<domain>/<!lists> does not exist.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/example.com/wrong')
        self.assertEqual(cm.exception.code, 404)

    def test_lists_are_deleted_when_domain_is_deleted(self):
        # /domains/<domain> DELETE removes all associated mailing lists.
        with transaction():
            create_list('ant@example.com')
        content, response = call_api(
            'http://localhost:9001/3.0/domains/example.com', method='DELETE')
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(getUtility(IListManager).get('ant@example.com'))

    def test_missing_domain(self):
        # You get a 404 if you try to access a nonexisting domain.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/does-not-exist.com')
        self.assertEqual(cm.exception.code, 404)

    def test_missing_domain_lists(self):
        # You get a 404 if you try to access the mailing lists of a
        # nonexisting domain.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/domains/does-not-exist.com/lists')
        self.assertEqual(cm.exception.code, 404)

    def test_create_existing_domain(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains', dict(
                mail_host='example.com',
                ))
        self.assertEqual(cm.exception.code, 400)

    def test_double_delete(self):
        # You cannot delete a domain twice.
        content, response = call_api(
            'http://localhost:9001/3.0/domains/example.com',
            method='DELETE')
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/example.com',
                     method='DELETE')
        self.assertEqual(cm.exception.code, 404)


class TestDomainOwners(unittest.TestCase):
    layer = RESTLayer

    def test_get_missing_domain_owners(self):
        # Try to get the owners of a missing domain.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/example.net/owners')
        self.assertEqual(cm.exception.code, 404)

    def test_bad_domain_owners_url(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/domains/example.com/owners/bogus')
        self.assertEqual(cm.exception.code, 404)

    def test_post_to_missing_domain_owners(self):
        # Try to add owners to a missing domain.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/example.net/owners', (
                ('owner', 'dave@example.com'), ('owner', 'elle@example.com'),
                ))
        self.assertEqual(cm.exception.code, 404)

    def test_delete_missing_domain_owners(self):
        # Try to delete the owners of a missing domain.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/example.net/owners',
                     method='DELETE')
        self.assertEqual(cm.exception.code, 404)

    def test_bad_post(self):
        # Send POST data with an invalid attribute.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/example.com/owners', (
                ('guy', 'dave@example.com'), ('gal', 'elle@example.com'),
                ))
        self.assertEqual(cm.exception.code, 400)

    def test_bad_delete(self):
        # Send DELETE with any data.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/example.com/owners', {
                'owner': 'dave@example.com',
                }, method='DELETE')
        self.assertEqual(cm.exception.code, 400)


class TestDomainTemplates(unittest.TestCase):
    """Test /domains/<mail-host>/uris"""

    layer = RESTLayer

    def test_no_templates_for_api_30(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/example.com/uris')
        self.assertEqual(cm.exception.code, 404)

    def test_no_templates_for_missing_list(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.1/domains/example.org/uris')
        self.assertEqual(cm.exception.code, 404)

    def test_path_too_long(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.1/domains/example.com/uris'
                     '/foo/bar')
        self.assertEqual(cm.exception.code, 400)

    def test_get_unknown_uri(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.1/domains/example.com/uris'
                     '/not:a:template')
        self.assertEqual(cm.exception.code, 404)

    def test_get_all_uris(self):
        manager = getUtility(ITemplateManager)
        with transaction():
            manager.set(
                'list:user:notice:welcome', 'example.com',
                'http://example.com/welcome')
            manager.set(
                'list:user:notice:goodbye', 'example.com',
                'http://example.com/goodbye',
                'a user', 'the password',
                )
        resource, response = call_api(
            'http://localhost:9001/3.1/domains/example.com/uris')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resource['start'], 0)
        self.assertEqual(resource['total_size'], 2)
        self.assertEqual(
            resource['self_link'],
            'http://localhost:9001/3.1/domains/example.com/uris')
        self.assertEqual(resource['entries'], [
            {'http_etag': '"e877ff896db0f2e280660ac16b9401f7925a53b9"',
             'name': 'list:user:notice:goodbye',
             'password': 'the password',
             'self_link': ('http://localhost:9001/3.1/domains/example.com'
                           '/uris/list:user:notice:goodbye'),
             'uri': 'http://example.com/goodbye',
             'username': 'a user',
             },
            {'http_etag': '"8dac25601c3419e98e2c05df1d962a2252b67ce6"',
             'name': 'list:user:notice:welcome',
             'self_link': ('http://localhost:9001/3.1/domains/example.com'
                           '/uris/list:user:notice:welcome'),
             'uri': 'http://example.com/welcome',
             }])

    def test_patch_uris(self):
        resource, response = call_api(
            'http://localhost:9001/3.1/domains/example.com/uris', {
                'list:user:notice:welcome': 'http://example.org/welcome',
                'list:user:notice:goodbye': 'http://example.org/goodbye',
                }, method='PATCH')
        self.assertEqual(response.status_code, 204)
        manager = getUtility(ITemplateManager)
        template = manager.raw('list:user:notice:welcome', 'example.com')
        self.assertEqual(template.uri, 'http://example.org/welcome')
        self.assertIsNone(template.username)
        self.assertEqual(template.password, '')
        template = manager.raw('list:user:notice:goodbye', 'example.com')
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertIsNone(template.username)
        self.assertEqual(template.password, '')

    def test_patch_uris_with_credentials(self):
        resource, response = call_api(
            'http://localhost:9001/3.1/domains/example.com/uris', {
                'list:user:notice:welcome': 'http://example.org/welcome',
                'list:user:notice:goodbye': 'http://example.org/goodbye',
                'password': 'some password',
                'username': 'anne.person',
                }, method='PATCH')
        self.assertEqual(response.status_code, 204)
        manager = getUtility(ITemplateManager)
        template = manager.raw('list:user:notice:welcome', 'example.com')
        self.assertEqual(template.uri, 'http://example.org/welcome')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:user:notice:goodbye', 'example.com')
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')

    def test_patch_uris_with_partial_credentials(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/domains/example.com/uris', {
                    'list:user:notice:welcome': 'http://example.org/welcome',
                    'list:user:notice:goodbye': 'http://example.org/goodbye',
                    'username': 'anne.person',
                    }, method='PATCH')
        self.assertEqual(cm.exception.code, 400)

    def test_put_all_uris(self):
        resource, response = call_api(
            'http://localhost:9001/3.1/domains/example.com/uris', {
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
        template = manager.raw('list:member:digest:footer', 'example.com')
        self.assertIsNone(template)
        template = manager.raw('list:member:digest:header', 'example.com')
        self.assertIsNone(template)
        template = manager.raw('list:member:regular:footer', 'example.com')
        self.assertEqual(template.uri, 'http://example.org/footer')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:member:regular:header', 'example.com')
        self.assertEqual(template.uri, 'http://example.org/header')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:user:notice:goodbye', 'example.com')
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:user:notice:goodbye', 'example.com')
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')

    def test_delete_all_uris(self):
        manager = getUtility(ITemplateManager)
        with transaction():
            manager.set(
                'list:user:notice:welcome', 'example.com',
                'http://example.com/welcome')
            manager.set(
                'list:user:notice:goodbye', 'example.com',
                'http://example.com/goodbye',
                'a user', 'the password',
                )
        resource, response = call_api(
            'http://localhost:9001/3.1/domains/example.com/uris',
            method='DELETE')
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(
            manager.raw('list:user:notice:welcome', 'example.com'))
        self.assertIsNone(
            manager.raw('list:user:notice:goodbye', 'example.com'))

    def test_get_a_url(self):
        with transaction():
            getUtility(ITemplateManager).set(
                'list:user:notice:welcome', 'example.com',
                'http://example.com/welcome')
        resource, response = call_api(
            'http://localhost:9001/3.1/domains/example.com/uris'
            '/list:user:notice:welcome')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resource, {
            'http_etag': '"8884a0b3d675b4cb9899a7825daac9db88b70bed"',
            'self_link': ('http://localhost:9001/3.1/domains/example.com'
                          '/uris/list:user:notice:welcome'),
            'uri': 'http://example.com/welcome',
            })

    def test_get_a_bad_url(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/domains/example.com/uris'
                '/list:user:notice:notemplate')
        self.assertEqual(cm.exception.code, 404)

    def test_get_unset_url(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/domains/example.com/uris'
                '/list:user:notice:welcome')
        self.assertEqual(cm.exception.code, 404)

    def test_patch_url_with_too_many_parameters(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/domains/example.com/uris', {
                    'list:user:notice:welcome': 'http://example.org/welcome',
                    'list:user:notice:goodbye': 'http://example.org/goodbye',
                    'secret': 'some password',
                    'person': 'anne.person',
                    }, method='PATCH')
        self.assertEqual(cm.exception.code, 400)
