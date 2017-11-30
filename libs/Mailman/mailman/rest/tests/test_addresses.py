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

"""REST address tests."""

import unittest

from mailman.app.lifecycle import create_list
from mailman.database.transaction import transaction
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import call_api, subscribe
from mailman.testing.layers import RESTLayer
from mailman.utilities.datetime import now
from urllib.error import HTTPError
from zope.component import getUtility


class TestAddresses(unittest.TestCase):
    layer = RESTLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('test@example.com')

    def test_no_addresses(self):
        # At first, there are no addresses.
        url = 'http://localhost:9001/3.0/addresses'
        json, response = call_api(url)
        self.assertEqual(json['start'], 0)
        self.assertEqual(json['total_size'], 0)

    def test_missing_address(self):
        # An address that isn't registered yet cannot be retrieved.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/addresses/nobody@example.com')
        self.assertEqual(cm.exception.code, 404)

    def test_membership_of_missing_address(self):
        # Try to get the memberships of a missing address.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/addresses/'
                     'nobody@example.com/memberships')
        self.assertEqual(cm.exception.code, 404)

    def test_membership_of_address_with_no_user(self):
        with transaction():
            getUtility(IUserManager).create_address('anne@example.com')
        json, content = call_api(
            'http://localhost:9001/3.0/addresses/anne@example.com/memberships')
        self.assertEqual(json['total_size'], 0)

    def test_verify_a_missing_address(self):
        # POSTing to the 'verify' sub-resource returns a 404.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/addresses/'
                     'nobody@example.com/verify', {})
        self.assertEqual(cm.exception.code, 404)

    def test_unverify_a_missing_address(self):
        # POSTing to the 'unverify' sub-resource returns a 404.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/addresses/'
                     'nobody@example.com/unverify', {})
        self.assertEqual(cm.exception.code, 404)

    def test_verify_already_verified(self):
        # It's okay to verify an already verified; it just doesn't change the
        # value.
        verified_on = now()
        with transaction():
            anne = getUtility(IUserManager).create_address('anne@example.com')
            anne.verified_on = verified_on
        json, response = call_api(
            'http://localhost:9001/3.0/addresses/anne@example.com/verify', {})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(anne.verified_on, verified_on)

    def test_unverify_already_unverified(self):
        # It's okay to unverify an already unverified; it just doesn't change
        # the value.
        with transaction():
            anne = getUtility(IUserManager).create_address('anne@example.com')
            self.assertEqual(anne.verified_on, None)
        json, response = call_api(
           'http://localhost:9001/3.0/addresses/anne@example.com/unverify', {})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(anne.verified_on, None)

    def test_verify_bad_request(self):
        # Too many segments after /verify.
        with transaction():
            anne = getUtility(IUserManager).create_address('anne@example.com')
            self.assertEqual(anne.verified_on, None)
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/addresses/'
                     'anne@example.com/verify/foo', {})
        self.assertEqual(cm.exception.code, 400)

    def test_unverify_bad_request(self):
        # Too many segments after /verify.
        with transaction():
            anne = getUtility(IUserManager).create_address('anne@example.com')
            self.assertEqual(anne.verified_on, None)
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/addresses/'
                     'anne@example.com/unverify/foo', {})
        self.assertEqual(cm.exception.code, 400)

    def test_address_added_to_user(self):
        # An address is added to a user record.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne@example.com')
        json, response = call_api(
            'http://localhost:9001/3.0/users/anne@example.com/addresses', {
                'email': 'anne.person@example.org',
                })
        self.assertIn('anne.person@example.org',
                      [addr.email for addr in anne.addresses])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.headers['location'],
            'http://localhost:9001/3.0/addresses/anne.person@example.org')
        # The address has no display name.
        anne_person = user_manager.get_address('anne.person@example.org')
        self.assertEqual(anne_person.display_name, '')

    def test_address_and_display_name_added_to_user(self):
        # Address with a display name is added to the user record.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne@example.com')
        json, response = call_api(
            'http://localhost:9001/3.0/users/anne@example.com/addresses', {
                'email': 'anne.person@example.org',
                'display_name': 'Ann E Person',
                })
        self.assertIn('anne.person@example.org',
                      [addr.email for addr in anne.addresses])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.headers['location'],
            'http://localhost:9001/3.0/addresses/anne.person@example.org')
        # The address has no display name.
        anne_person = user_manager.get_address('anne.person@example.org')
        self.assertEqual(anne_person.display_name, 'Ann E Person')

    def test_existing_address_bad_request(self):
        # Trying to add an existing address returns 400.
        with transaction():
            getUtility(IUserManager).create_user('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/users/anne@example.com/addresses', {
                     'email': 'anne@example.com',
                     })
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason, 'Address belongs to other user')

    def test_add_unlinked_address_to_user(self):
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne.person@example.com')
            user_manager.create_address('anne@example.com')
        json, response = call_api(
         'http://localhost:9001/3.0/users/anne.person@example.com/addresses', {
            'email': 'anne@example.com',
            })
        self.assertIn('anne@example.com',
                      [address.email for address in anne.addresses])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.headers['location'],
            'http://localhost:9001/3.0/addresses/anne@example.com')
        # The address has no display name.
        anne_person = user_manager.get_address('anne@example.com')
        self.assertEqual(anne_person.display_name, '')

    def test_add_unlinked_address_to_user_with_ignored_display_name(self):
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne.person@example.com')
            user_manager.create_address('anne@example.com')
        json, response = call_api(
         'http://localhost:9001/3.0/users/anne.person@example.com/addresses', {
            'email': 'anne@example.com',
            'display_name': 'Anne Person',
            })
        self.assertIn('anne@example.com',
                      [address.email for address in anne.addresses])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.headers['location'],
            'http://localhost:9001/3.0/addresses/anne@example.com')
        # Even though a display_name was given in the POST data, because the
        # address already existed, it still has no display name.
        anne_person = user_manager.get_address('anne@example.com')
        self.assertEqual(anne_person.display_name, '')

    def test_existing_address_absorb(self):
        # Trying to add an existing address causes a merge if the
        # 'absorb_existing' flag is present.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne@example.com')
            user_manager.create_user('bart@example.com')
        json, response = call_api(
            'http://localhost:9001/3.0/users/anne@example.com/addresses', {
                 'email': 'bart@example.com',
                 'absorb_existing': True,
                 })
        self.assertIn('bart@example.com',
                      [address.email for address in anne.addresses])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.headers['location'],
            'http://localhost:9001/3.0/addresses/bart@example.com')

    def test_invalid_address_bad_request(self):
        # Trying to add an invalid address string returns 400.
        with transaction():
            getUtility(IUserManager).create_user('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/users/anne@example.com/addresses', {
                     'email': 'invalid_address_string'
                     })
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason, 'Invalid email address')

    def test_empty_address_bad_request(self):
        # The address is required.
        with transaction():
            getUtility(IUserManager).create_user('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/users/anne@example.com/addresses',
                {})
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason, 'Missing parameters: email')

    def test_get_addresses_of_missing_user(self):
        # There is no user associated with the given address.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/users/anne@example.com/addresses')
        self.assertEqual(cm.exception.code, 404)

    def test_add_address_to_missing_user(self):
        # The user that the address is being added to must exist.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/users/anne@example.com/addresses', {
                    'email': 'anne.person@example.org',
                    })
        self.assertEqual(cm.exception.code, 404)

    def test_address_with_user(self):
        # An address which is already linked to a user has a 'user' key in the
        # JSON representation.
        with transaction():
            getUtility(IUserManager).create_user('anne@example.com')
        json, response = call_api(
            'http://localhost:9001/3.0/addresses/anne@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['user'], 'http://localhost:9001/3.0/users/1')

    def test_address_without_user(self):
        # The 'user' key is missing from the JSON representation of an address
        # with no linked user.
        with transaction():
            getUtility(IUserManager).create_address('anne@example.com')
        json, response = call_api(
            'http://localhost:9001/3.0/addresses/anne@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('user', json)

    def test_user_subresource_on_unlinked_address(self):
        # Trying to access the 'user' subresource on an address that is not
        # linked to a user will return a 404 error.
        with transaction():
            getUtility(IUserManager).create_address('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/addresses/anne@example.com/user')
        self.assertEqual(cm.exception.code, 404)

    def test_user_subresource(self):
        # For an address which is linked to a user, accessing the user
        # subresource of the address path returns the user JSON representation.
        user_manager = getUtility(IUserManager)
        with transaction():
            user_manager.create_user('anne@example.com', 'Anne')
        json, response = call_api(
            'http://localhost:9001/3.0/addresses/anne@example.com/user')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['user_id'], 1)
        self.assertEqual(json['display_name'], 'Anne')
        user_resource = json['self_link']
        self.assertEqual(user_resource, 'http://localhost:9001/3.0/users/1')
        # The self_link points to the correct user.
        json, response = call_api(user_resource)
        self.assertEqual(json['user_id'], 1)
        self.assertEqual(json['display_name'], 'Anne')
        self.assertEqual(json['self_link'], user_resource)

    def test_user_subresource_post(self):
        # If the address is not yet linked to a user, POSTing a user id to the
        # 'user' subresource links the address to the given user.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne.person@example.org', 'Anne')
            anne_addr = user_manager.create_address('anne@example.com')
        json, response = call_api(
            'http://localhost:9001/3.0/addresses/anne@example.com/user', {
                'user_id': anne.user_id.int,
                })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(anne_addr.user, anne)
        self.assertEqual(sorted([a.email for a in anne.addresses]),
                         ['anne.person@example.org', 'anne@example.com'])

    def test_user_subresource_post_new_user(self):
        # If the address is not yet linked to a user, POSTing to the 'user'
        # subresources creates a new user object and links it to the address.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne_addr = user_manager.create_address('anne@example.com')
        json, response = call_api(
            'http://localhost:9001/3.0/addresses/anne@example.com/user', {
                'display_name': 'Anne',
                })
        self.assertEqual(response.status_code, 201)
        anne = user_manager.get_user('anne@example.com')
        self.assertIsNotNone(anne)
        self.assertEqual(anne.display_name, 'Anne')
        self.assertEqual([a.email for a in anne.addresses],
                         ['anne@example.com'])
        self.assertEqual(anne_addr.user, anne)
        self.assertEqual(response.headers['location'],
                         'http://localhost:9001/3.0/users/1')

    def test_user_subresource_post_conflict(self):
        # If the address is already linked to a user, trying to link it to
        # another user produces a 409 Conflict error.
        with transaction():
            getUtility(IUserManager).create_user('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/addresses/anne@example.com/user', {
                    'email': 'anne.person@example.org',
                    })
        self.assertEqual(cm.exception.code, 409)

    def test_user_subresource_post_new_user_no_auto_create(self):
        # By default, POSTing to the 'user' resource of an unlinked address
        # will automatically create the user.  By setting a boolean
        # 'auto_create' flag to false, you can prevent this.
        with transaction():
            getUtility(IUserManager).create_address('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/addresses/anne@example.com/user', {
                    'display_name': 'Anne',
                    'auto_create': 0,
                    })
        self.assertEqual(cm.exception.code, 403)

    def test_user_subresource_post_no_such_user(self):
        # Try to link an address to a nonexistent user.
        with transaction():
            getUtility(IUserManager).create_address('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/addresses/anne@example.com/user', {
                    'user_id': 2,
                    })
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason, 'No user with ID 2')

    def test_user_subresource_unlink(self):
        # By DELETEing the usr subresource, you can unlink a user from an
        # address.
        user_manager = getUtility(IUserManager)
        with transaction():
            user_manager.create_user('anne@example.com')
        json, response = call_api(
            'http://localhost:9001/3.0/addresses/anne@example.com/user',
            method='DELETE')
        self.assertEqual(response.status_code, 204)
        anne_addr = user_manager.get_address('anne@example.com')
        self.assertIsNone(anne_addr.user, 'The address is still linked')
        self.assertIsNone(user_manager.get_user('anne@example.com'))

    def test_user_subresource_unlink_unlinked(self):
        # If you try to unlink an unlinked address, you get a 404 error.
        user_manager = getUtility(IUserManager)
        with transaction():
            user_manager.create_address('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/addresses/anne@example.com/user',
                method='DELETE')
        self.assertEqual(cm.exception.code, 404)

    def test_user_subresource_put(self):
        # By PUTing to the 'user' resource, you can change the user that an
        # address is linked to.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne@example.com', 'Anne')
            bart = user_manager.create_user(display_name='Bart')
        json, response = call_api(
            'http://localhost:9001/3.0/addresses/anne@example.com/user', {
                'user_id': bart.user_id.int,
                }, method='PUT')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(anne.addresses, [])
        self.assertEqual([address.email for address in bart.addresses],
                         ['anne@example.com'])
        self.assertEqual(bart,
                         user_manager.get_address('anne@example.com').user)

    def test_user_subresource_put_create(self):
        # PUTing to the 'user' resource creates the user, just like with POST.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne@example.com', 'Anne')
        json, response = call_api(
            'http://localhost:9001/3.0/addresses/anne@example.com/user', {
                'email': 'anne.person@example.org',
                }, method='PUT')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(anne.addresses, [])
        anne_person = user_manager.get_user('anne.person@example.org')
        self.assertIsNotNone(anne_person)
        self.assertEqual(
            sorted([address.email for address in anne_person.addresses]),
            ['anne.person@example.org', 'anne@example.com'])
        anne_addr = user_manager.get_address('anne@example.com')
        self.assertIsNotNone(anne_addr)
        self.assertEqual(anne_addr.user, anne_person)

    def test_delete_missing_address(self):
        # DELETEing an address through the REST API that doesn't exist returns
        # a 404 error.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/addresses/anne@example.com',
                method='DELETE')
        self.assertEqual(cm.exception.code, 404)

    def test_bad_memberships_url(self):
        with transaction():
            subscribe(self._mlist, 'Anne')
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/addresses/'
                     'aperson@example.com/memberships/bogus')
        self.assertEqual(cm.exception.code, 404)

    def test_bad_preferences_url(self):
        with transaction():
            subscribe(self._mlist, 'Anne')
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/addresses/'
                     'aperson@example.com/preferences/bogus')
        self.assertEqual(cm.exception.code, 404)

    def test_bad_preferences_address(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/addresses/'
                     'nobody@example.com/preferences')
        self.assertEqual(cm.exception.code, 404)

    def test_bad_user_address(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/addresses/'
                     'nobody@example.com/user')
        self.assertEqual(cm.exception.code, 404)

    def test_bad_user_addresses_url(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/'
                     'nobody@example.com/addresses')
        self.assertEqual(cm.exception.code, 404)


class TestAPI31Addresses(unittest.TestCase):
    """UUIDs are represented as hex instead of int in API 3.1

    See issue #121 for details.  This is a deliberately backward
    incompatible change.
    """

    layer = RESTLayer

    def test_address_user_id_is_hex(self):
        user_manager = getUtility(IUserManager)
        with transaction():
            user_manager.create_user('anne@example.com', 'Anne')
        json, response = call_api(
            'http://localhost:9001/3.1/addresses/anne@example.com')
        self.assertEqual(
            json['user'],
            'http://localhost:9001/3.1/users/00000000000000000000000000000001')

    def test_addresses_user_ids_are_hex(self):
        user_manager = getUtility(IUserManager)
        # Do this sequentially so we're sure which user gets which uid.
        with transaction():
            user_manager.create_user('anne@example.com', 'Anne')
        with transaction():
            user_manager.create_user('bart@example.com', 'Bart')
        json, response = call_api('http://localhost:9001/3.1/addresses')
        entries = json['entries']
        self.assertEqual(
            entries[0]['user'],
            'http://localhost:9001/3.1/users/00000000000000000000000000000001')
        self.assertEqual(
            entries[1]['user'],
            'http://localhost:9001/3.1/users/00000000000000000000000000000002')

    def test_user_subresource_post(self):
        # If the address is not yet linked to a user, POSTing a user id to the
        # 'user' subresource links the address to the given user.  In
        # API 3.0, the user id must be the hex representation.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne.person@example.org', 'Anne')
            anne_addr = user_manager.create_address('anne@example.com')
        json, response = call_api(
            'http://localhost:9001/3.1/addresses/anne@example.com/user', {
                'user_id': anne.user_id.hex,
                })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(anne_addr.user, anne)
        self.assertEqual(sorted([a.email for a in anne.addresses]),
                         ['anne.person@example.org', 'anne@example.com'])

    def test_user_subresource_cannot_post_int(self):
        # If the address is not yet linked to a user, POSTing a user id to the
        # 'user' subresource links the address to the given user.  In
        # API 3.1, the user id must be the hex representation.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne.person@example.org', 'Anne')
            user_manager.create_address('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/addresses/anne@example.com/user', {
                    'user_id': anne.user_id.int,
                    })
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason,
                         'Cannot convert parameters: user_id')

    def test_user_subresource_put(self):
        # By PUTing to the 'user' resource, you can change the user that an
        # address is linked to.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne@example.com', 'Anne')
            bart = user_manager.create_user(display_name='Bart')
        json, response = call_api(
            'http://localhost:9001/3.1/addresses/anne@example.com/user', {
                'user_id': bart.user_id.hex,
                }, method='PUT')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(anne.addresses, [])
        self.assertEqual([address.email for address in bart.addresses],
                         ['anne@example.com'])
        self.assertEqual(bart,
                         user_manager.get_address('anne@example.com').user)

    def test_user_subresource_cannot_put_int(self):
        # If the address is not yet linked to a user, POSTing a user id to the
        # 'user' subresource links the address to the given user.  In
        # API 3.1, the user id must be the hex representation.
        user_manager = getUtility(IUserManager)
        with transaction():
            anne = user_manager.create_user('anne.person@example.org', 'Anne')
            user_manager.create_address('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/addresses/anne@example.com/user', {
                    'user_id': anne.user_id.int,
                    }, method='PUT')
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason,
                         'Cannot convert parameters: user_id')
