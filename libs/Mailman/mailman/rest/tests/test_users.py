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

"""REST user tests."""

import os
import unittest

from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.database.transaction import transaction
from mailman.interfaces.member import DeliveryMode
from mailman.interfaces.usermanager import IUserManager
from mailman.model.preferences import Preferences
from mailman.testing.helpers import call_api, configuration
from mailman.testing.layers import RESTLayer
from urllib.error import HTTPError
from zope.component import getUtility


class TestUsers(unittest.TestCase):
    layer = RESTLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('test@example.com')

    def test_get_missing_user_by_id(self):
        # You can't GET a missing user by user id.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/99')
        self.assertEqual(cm.exception.code, 404)

    def test_get_missing_user_by_address(self):
        # You can't GET a missing user by address.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/missing@example.org')
        self.assertEqual(cm.exception.code, 404)

    def test_patch_missing_user_by_id(self):
        # You can't PATCH a missing user by user id.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/99', {
                     'display_name': 'Bob Dobbs',
                     }, method='PATCH')
        self.assertEqual(cm.exception.code, 404)

    def test_patch_missing_user_by_address(self):
        # You can't PATCH a missing user by user address.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/bob@example.org', {
                     'display_name': 'Bob Dobbs',
                     }, method='PATCH')
        self.assertEqual(cm.exception.code, 404)

    def test_put_missing_user_by_id(self):
        # You can't PUT a missing user by user id.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/99', {
                     'display_name': 'Bob Dobbs',
                     'cleartext_password': 'abc123',
                     }, method='PUT')
        self.assertEqual(cm.exception.code, 404)

    def test_put_missing_user_by_address(self):
        # You can't PUT a missing user by user address.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/bob@example.org', {
                     'display_name': 'Bob Dobbs',
                     'cleartext_password': 'abc123',
                     }, method='PUT')
        self.assertEqual(cm.exception.code, 404)

    def test_delete_missing_user_by_id(self):
        # You can't DELETE a missing user by user id.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/99', method='DELETE')
        self.assertEqual(cm.exception.code, 404)

    def test_delete_missing_user_by_address(self):
        # You can't DELETE a missing user by user address.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/bob@example.com',
                     method='DELETE')
        self.assertEqual(cm.exception.code, 404)

    def test_delete_user_twice(self):
        # You cannot DELETE a user twice, either by address or user id.
        with transaction():
            anne = getUtility(IUserManager).create_user(
                'anne@example.com', 'Anne Person')
            user_id = anne.user_id
        json, response = call_api(
            'http://localhost:9001/3.0/users/anne@example.com',
            method='DELETE')
        self.assertEqual(response.status_code, 204)
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/anne@example.com',
                     method='DELETE')
        self.assertEqual(cm.exception.code, 404)
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/{}'.format(user_id),
                     method='DELETE')
        self.assertEqual(cm.exception.code, 404)

    def test_get_after_delete(self):
        # You cannot GET a user record after deleting them.
        with transaction():
            anne = getUtility(IUserManager).create_user(
                'anne@example.com', 'Anne Person')
            user_id = anne.user_id
        # You can still GET the user record.
        json, response = call_api(
            'http://localhost:9001/3.0/users/anne@example.com')
        self.assertEqual(response.status_code, 200)
        # Delete the user.
        json, response = call_api(
            'http://localhost:9001/3.0/users/anne@example.com',
            method='DELETE')
        self.assertEqual(response.status_code, 204)
        # The user record can no longer be retrieved.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/anne@example.com')
        self.assertEqual(cm.exception.code, 404)
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/{}'.format(user_id))
        self.assertEqual(cm.exception.code, 404)

    def test_existing_user_error(self):
        # Creating a user twice results in an error.
        call_api('http://localhost:9001/3.0/users', {
                 'email': 'anne@example.com',
                 })
        # The second try returns an error.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users', {
                     'email': 'anne@example.com',
                     })
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason,
                         'User already exists: anne@example.com')

    def test_addresses_of_missing_user_id(self):
        # Trying to get the /addresses of a missing user id results in error.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/801/addresses')
        self.assertEqual(cm.exception.code, 404)

    def test_addresses_of_missing_user_address(self):
        # Trying to get the /addresses of a missing user id results in error.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/z@example.net/addresses')
        self.assertEqual(cm.exception.code, 404)

    def test_login_missing_user_by_id(self):
        # Verify a password for a non-existing user, by id.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/99/login', {
                     'cleartext_password': 'wrong',
                     })
        self.assertEqual(cm.exception.code, 404)

    def test_login_missing_user_by_address(self):
        # Verify a password for a non-existing user, by address.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/z@example.org/login', {
                     'cleartext_password': 'wrong',
                     })
        self.assertEqual(cm.exception.code, 404)

    def test_existing_address_link(self):
        # Creating a user with an existing address links them.
        user_manager = getUtility(IUserManager)
        with transaction():
            user_manager.create_address('anne@example.com')
        call_api('http://localhost:9001/3.0/users', dict(
            email='anne@example.com',
            ))
        anne = user_manager.get_user('anne@example.com')
        self.assertEqual(anne.display_name, '')
        self.assertFalse(anne.is_server_owner)
        self.assertIn('anne@example.com',
                      [address.email for address in anne.addresses])

    def test_existing_address_link_with_arguments(self):
        # Creating a user with an existing address links them, and the
        # addition arguments get honored.
        user_manager = getUtility(IUserManager)
        with transaction():
            user_manager.create_address('anne@example.com')
        call_api('http://localhost:9001/3.0/users', dict(
            email='anne@example.com',
            display_name='Anne Person',
            password='123',
            is_server_owner=True,
            ))
        anne = user_manager.get_user('anne@example.com')
        self.assertEqual(anne.display_name, 'Anne Person')
        self.assertTrue(anne.is_server_owner)
        self.assertEqual(anne.password, '{plaintext}123')
        self.assertIn('anne@example.com',
                      [address.email for address in anne.addresses])

    def test_create_user_twice(self):
        # LP: #1418280.  No additional users should be created when an address
        # that already exists is given.
        json, response = call_api('http://localhost:9001/3.0/users')
        self.assertEqual(json['total_size'], 0)
        # Create the user.
        call_api('http://localhost:9001/3.0/users', dict(
            email='anne@example.com'))
        # There is now one user.
        json, response = call_api('http://localhost:9001/3.0/users')
        self.assertEqual(json['total_size'], 1)
        # Trying to create the user with the same address results in an error.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users', dict(
                email='anne@example.com'))
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason,
                         'User already exists: anne@example.com')
        # But at least no new users was created.
        json, response = call_api('http://localhost:9001/3.0/users')
        self.assertEqual(json['total_size'], 1)

    def test_create_server_owner_false(self):
        # Issue #136: Creating a user with is_server_owner=no should create
        # user who is not a server owner.
        json, response = call_api('http://localhost:9001/3.0/users', dict(
            email='anne@example.com',
            is_server_owner='no'))
        anne = getUtility(IUserManager).get_user('anne@example.com')
        self.assertFalse(anne.is_server_owner)

    def test_create_server_owner_true(self):
        # Issue #136: Creating a user with is_server_owner=yes should create a
        # new server owner user.
        json, response = call_api('http://localhost:9001/3.0/users', dict(
            email='anne@example.com',
            is_server_owner='yes'))
        anne = getUtility(IUserManager).get_user('anne@example.com')
        self.assertTrue(anne.is_server_owner)

    def test_create_server_owner_bogus(self):
        # Issue #136: Creating a user with is_server_owner=bogus should throw
        # an exception.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users', dict(
                email='anne@example.com',
                is_server_owner='bogus'))
        self.assertEqual(cm.exception.code, 400)

    def test_preferences_deletion_on_user_deletion(self):
        # LP: #1418276 - deleting a user did not delete their preferences.
        with transaction():
            anne = getUtility(IUserManager).create_user(
                'anne@example.com', 'Anne Person')
        # Anne's preference is in the database.
        preferences = config.db.store.query(Preferences).filter_by(
            id=anne.preferences.id)
        self.assertEqual(preferences.count(), 1)
        # Delete the user via REST.
        json, response = call_api(
            'http://localhost:9001/3.0/users/anne@example.com',
            method='DELETE')
        self.assertEqual(response.status_code, 204)
        # The user's preference has been deleted.
        with transaction():
            preferences = config.db.store.query(Preferences).filter_by(
                id=anne.preferences.id)
            self.assertEqual(preferences.count(), 0)

    def test_preferences_self_link(self):
        with transaction():
            user = getUtility(IUserManager).create_user('anne@example.com')
            user.preferences.delivery_mode = DeliveryMode.summary_digests
        json, response = call_api(
            'http://localhost:9001/3.0/users/1/preferences')
        self.assertEqual(
            json['self_link'],
            'http://localhost:9001/3.0/users/1/preferences')


class TestLogin(unittest.TestCase):
    """Test user 'login' (really just password verification)."""

    layer = RESTLayer

    def setUp(self):
        user_manager = getUtility(IUserManager)
        with transaction():
            self.anne = user_manager.create_user(
                'anne@example.com', 'Anne Person')
            self.anne.password = config.password_context.encrypt('abc123')

    def test_login_with_cleartext_password(self):
        # A user can log in with the correct clear text password.
        json, response = call_api(
            'http://localhost:9001/3.0/users/anne@example.com/login', {
                'cleartext_password': 'abc123',
                }, method='POST')
        self.assertEqual(response.status_code, 204)
        # But the user cannot log in with an incorrect password.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/users/anne@example.com/login', {
                    'cleartext_password': 'not-the-password',
                    }, method='POST')
        self.assertEqual(cm.exception.code, 403)

    def test_wrong_parameter(self):
        # A bad request because it is mistyped the required attribute.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/1/login', {
                     'hashed_password': 'bad hash',
                     })
        self.assertEqual(cm.exception.code, 400)

    def test_not_enough_parameters(self):
        # A bad request because it is missing the required attribute.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/1/login', {
                     })
        self.assertEqual(cm.exception.code, 400)

    def test_too_many_parameters(self):
        # A bad request because it has too many attributes.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/users/1/login', {
                     'cleartext_password': 'abc123',
                     'display_name': 'Annie Personhood',
                     })
        self.assertEqual(cm.exception.code, 400)

    def test_successful_login_updates_password(self):
        # Passlib supports updating the hash when the hash algorithm changes.
        # When a user logs in successfully, the password will be updated if
        # necessary.
        #
        # Start by hashing Anne's password with a different hashing algorithm
        # than the one that the REST runner uses by default during testing.
        config_file = os.path.join(config.VAR_DIR, 'passlib-tmp.config')
        with open(config_file, 'w') as fp:
            print("""\
[passlib]
schemes = hex_md5
""", file=fp)
        with configuration('passwords', configuration=config_file):
            with transaction():
                self.anne.password = config.password_context.encrypt('abc123')
                # Just ensure Anne's password is hashed correctly.
                self.assertEqual(self.anne.password,
                                 'e99a18c428cb38d5f260853678922e03')
        # Now, Anne logs in with a successful password.  This should change it
        # back to the plaintext hash.
        call_api('http://localhost:9001/3.0/users/1/login', {
                 'cleartext_password': 'abc123',
                 })
        self.assertEqual(self.anne.password, '{plaintext}abc123')


class TestLP1074374(unittest.TestCase):
    """LP: #1074374 - deleting a user left their address records active."""

    layer = RESTLayer

    def setUp(self):
        self.user_manager = getUtility(IUserManager)
        with transaction():
            self.mlist = create_list('test@example.com')
            self.anne = self.user_manager.create_user(
                'anne@example.com', 'Anne Person')

    def test_deleting_user_deletes_address(self):
        with transaction():
            user_id = self.anne.user_id
        call_api('http://localhost:9001/3.0/users/anne@example.com',
                 method='DELETE')
        # The user record is gone.
        self.assertIsNone(self.user_manager.get_user_by_id(user_id))
        self.assertIsNone(self.user_manager.get_user('anne@example.com'))
        # Anne's address is also gone.
        self.assertIsNone(self.user_manager.get_address('anne@example.com'))

    def test_deleting_user_deletes_addresses(self):
        # All of Anne's linked addresses are deleted when her user record is
        # deleted.  So, register and link another address to Anne.
        with transaction():
            self.anne.register('aperson@example.org')
        call_api('http://localhost:9001/3.0/users/anne@example.com',
                 method='DELETE')
        self.assertIsNone(self.user_manager.get_user('anne@example.com'))
        self.assertIsNone(self.user_manager.get_user('aperson@example.org'))

    def test_lp_1074374(self):
        # Specific steps to reproduce the bug:
        # - create a user through the REST API (well, we did that outside the
        #   REST API here, but that should be fine)
        # - delete that user through the API
        # - repeating step 1 gives a 500 status code
        # - /3.0/addresses still contains the original address
        # - /3.0/members gives a 500
        with transaction():
            user_id = self.anne.user_id
            address = list(self.anne.addresses)[0]
            self.mlist.subscribe(address)
        call_api('http://localhost:9001/3.0/users/anne@example.com',
                 method='DELETE')
        json, response = call_api('http://localhost:9001/3.0/addresses')
        # There are no addresses, and thus no entries in the returned JSON.
        self.assertNotIn('entries', json)
        self.assertEqual(json['total_size'], 0)
        # There are also no members.
        json, response = call_api('http://localhost:9001/3.0/members')
        self.assertNotIn('entries', json)
        self.assertEqual(json['total_size'], 0)
        # Now we can create a new user record for Anne, and subscribe her to
        # the mailing list, this time all through the API.
        call_api('http://localhost:9001/3.0/users', dict(
            email='anne@example.com',
            password='bbb'))
        call_api('http://localhost:9001/3.0/members', dict(
            list_id='test.example.com',
            subscriber='anne@example.com',
            role='member',
            pre_verified=True, pre_confirmed=True, pre_approved=True))
        # This is not the Anne you're looking for.  (IOW, the new Anne is a
        # different user).
        json, response = call_api(
            'http://localhost:9001/3.0/users/anne@example.com')
        self.assertNotEqual(user_id, json['user_id'])
        # Anne has an address record.
        json, response = call_api('http://localhost:9001/3.0/addresses')
        self.assertEqual(json['total_size'], 1)
        self.assertEqual(json['entries'][0]['email'], 'anne@example.com')
        # Anne is also a member of the mailing list.
        json, response = call_api('http://localhost:9001/3.0/members')
        self.assertEqual(json['total_size'], 1)
        member = json['entries'][0]
        self.assertEqual(
            member['address'],
            'http://localhost:9001/3.0/addresses/anne@example.com')
        self.assertEqual(member['email'], 'anne@example.com')
        self.assertEqual(member['delivery_mode'], 'regular')
        self.assertEqual(member['list_id'], 'test.example.com')
        self.assertEqual(member['role'], 'member')


class TestLP1419519(unittest.TestCase):
    # LP: #1419519 - deleting a user with many linked addresses does not delete
    # all address records.
    layer = RESTLayer

    def setUp(self):
        # Create a user and link 10 addresses to that user.
        self.manager = getUtility(IUserManager)
        with transaction():
            anne = self.manager.create_user('anne@example.com', 'Anne Person')
            for i in range(10):
                email = 'a{:02d}@example.com'.format(i)
                address = self.manager.create_address(email)
                anne.link(address)

    def test_delete_user(self):
        # Deleting the user deletes all their linked addresses.
        #
        # We start with 11 addresses in the database.
        emails = sorted(address.email for address in self.manager.addresses)
        self.assertEqual(emails, [
            'a00@example.com',
            'a01@example.com',
            'a02@example.com',
            'a03@example.com',
            'a04@example.com',
            'a05@example.com',
            'a06@example.com',
            'a07@example.com',
            'a08@example.com',
            'a09@example.com',
            'anne@example.com',
            ])
        json, response = call_api(
            'http://localhost:9001/3.0/users/anne@example.com',
            method='DELETE')
        self.assertEqual(response.status_code, 204)
        # Now there should be no addresses in the database.
        config.db.abort()
        emails = sorted(address.email for address in self.manager.addresses)
        self.assertEqual(len(emails), 0)


class TestAPI31Users(unittest.TestCase):
    """UUIDs are represented as hex in API 3.1."""

    layer = RESTLayer

    def test_get_user(self):
        with transaction():
            getUtility(IUserManager).create_user('anne@example.com')
        json, response = call_api(
            'http://localhost:9001/3.1/users/00000000000000000000000000000001')
        self.assertEqual(
            json['user_id'], '00000000000000000000000000000001')
        self.assertEqual(
            json['self_link'],
            'http://localhost:9001/3.1/users/00000000000000000000000000000001')

    def test_cannot_get_user_by_int(self):
        with transaction():
            getUtility(IUserManager).create_user('anne@example.com')
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.1/users/1')
        self.assertEqual(cm.exception.code, 404)

    def test_get_all_users(self):
        user_manager = getUtility(IUserManager)
        with transaction():
            user_manager.create_user('anne@example.com')
            user_manager.create_user('bart@example.com')
        json, response = call_api('http://localhost:9001/3.1/users')
        entries = json['entries']
        self.assertEqual(len(entries), 2)
        self.assertEqual(
            entries[0]['user_id'], '00000000000000000000000000000001')
        self.assertEqual(
            entries[0]['self_link'],
            'http://localhost:9001/3.1/users/00000000000000000000000000000001')
        self.assertEqual(
            entries[1]['user_id'], '00000000000000000000000000000002')
        self.assertEqual(
            entries[1]['self_link'],
            'http://localhost:9001/3.1/users/00000000000000000000000000000002')

    def test_create_user(self):
        json, response = call_api(
            'http://localhost:9001/3.1/users', {
                'email': 'anne@example.com',
                })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.headers['location'],
            'http://localhost:9001/3.1/users/00000000000000000000000000000001')

    def test_preferences_self_link(self):
        with transaction():
            user = getUtility(IUserManager).create_user('anne@example.com')
            user.preferences.delivery_mode = DeliveryMode.summary_digests
        json, response = call_api(
            'http://localhost:9001/3.1/users'
            '/00000000000000000000000000000001/preferences')
        self.assertEqual(
            json['self_link'],
            'http://localhost:9001/3.1/users'
            '/00000000000000000000000000000001/preferences')
