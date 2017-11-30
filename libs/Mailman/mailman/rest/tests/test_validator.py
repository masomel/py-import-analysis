# Copyright (C) 2015-2017 by the Free Software Foundation, Inc.
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

"""Test REST validators."""

import unittest

from mailman.core.api import API30, API31
from mailman.interfaces.action import Action
from mailman.interfaces.usermanager import IUserManager
from mailman.rest.validator import (
    enum_validator, list_of_strings_validator, subscriber_validator)
from mailman.testing.layers import RESTLayer
from zope.component import getUtility


class TestValidators(unittest.TestCase):
    layer = RESTLayer

    def test_list_of_strings_validator_single(self):
        # This validator should turn a single key into a list of keys.
        self.assertEqual(list_of_strings_validator('ant'), ['ant'])

    def test_list_of_strings_validator_multiple(self):
        # This validator should turn a single key into a list of keys.
        self.assertEqual(
            list_of_strings_validator(['ant', 'bee', 'cat']),
            ['ant', 'bee', 'cat'])

    def test_list_of_strings_validator_invalid(self):
        # Strings are required.
        self.assertRaises(ValueError, list_of_strings_validator, 7)
        self.assertRaises(ValueError, list_of_strings_validator, ['ant', 7])

    def test_subscriber_validator_int_uuid(self):
        # Convert from an existing user id to a UUID.
        anne = getUtility(IUserManager).make_user('anne@example.com')
        uuid = subscriber_validator(API30)(str(anne.user_id.int))
        self.assertEqual(anne.user_id, uuid)

    def test_subscriber_validator_hex_uuid(self):
        # Convert from an existing user id to a UUID.
        anne = getUtility(IUserManager).make_user('anne@example.com')
        uuid = subscriber_validator(API31)(anne.user_id.hex)
        self.assertEqual(anne.user_id, uuid)

    def test_subscriber_validator_no_int_uuid(self):
        # API 3.1 does not accept ints as subscriber id's.
        anne = getUtility(IUserManager).make_user('anne@example.com')
        self.assertRaises(ValueError,
                          subscriber_validator(API31), str(anne.user_id.int))

    def test_subscriber_validator_bad_int_uuid(self):
        # In API 3.0, UUIDs are ints.
        self.assertRaises(ValueError,
                          subscriber_validator(API30), 'not-a-thing')

    def test_subscriber_validator_bad_int_hex(self):
        # In API 3.1, UUIDs are hexes.
        self.assertRaises(ValueError,
                          subscriber_validator(API31), 'not-a-thing')

    def test_subscriber_validator_email_address_API30(self):
        self.assertEqual(subscriber_validator(API30)('anne@example.com'),
                         'anne@example.com')

    def test_subscriber_validator_email_address_API31(self):
        self.assertEqual(subscriber_validator(API31)('anne@example.com'),
                         'anne@example.com')

    def test_enum_validator_valid(self):
        self.assertEqual(enum_validator(Action)('hold'), Action.hold)

    def test_enum_validator_invalid(self):
        self.assertRaises(ValueError,
                          enum_validator(Action), 'not-a-thing')

    def test_enum_validator_blank(self):
        self.assertEqual(enum_validator(Action, allow_blank=True)(''), None)
