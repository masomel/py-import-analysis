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

"""Test addresses."""

import unittest

from mailman.email.validate import InvalidEmailAddressError
from mailman.interfaces.address import ExistingAddressError
from mailman.interfaces.usermanager import IUserManager
from mailman.model.address import Address
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestAddress(unittest.TestCase):
    """Test addresses."""

    layer = ConfigLayer

    def setUp(self):
        self._usermgr = getUtility(IUserManager)
        self._address = self._usermgr.create_address('FPERSON@example.com')

    def test_invalid_email_string_raises_exception(self):
        self.assertRaises(InvalidEmailAddressError,
                          Address, 'not_a_valid_email_string', '')

    def test_no_local_email_string_raises_exception(self):
        self.assertRaises(InvalidEmailAddressError,
                          Address, '@example.com', '')

    def test_space_in_email_string_raises_exception(self):
        self.assertRaises(InvalidEmailAddressError,
                          Address, 'us er@example.com', '')

    def test_non_ascii_email_local_part_raises_exception(self):
        self.assertRaises(InvalidEmailAddressError,
                          Address, 'us\xe9r@example.com', '')

    def test_non_ascii_email_domain_raises_exception(self):
        self.assertRaises(InvalidEmailAddressError,
                          Address, 'user@\xe9xample.com', '')

    def test_leading_hyphen_email_domain_raises_exception(self):
        self.assertRaises(InvalidEmailAddressError,
                          Address, 'user@example.-com', '')

    def test_empty_part_email_domain_raises_exception(self):
        self.assertRaises(InvalidEmailAddressError,
                          Address, 'user@example..com', '')

    def test_bad_ascii_email_domain_raises_exception(self):
        self.assertRaises(InvalidEmailAddressError,
                          Address, 'user@x_example.com', '')

    def test_high_unicode_email_local_part_raises_exception(self):
        self.assertRaises(InvalidEmailAddressError,
                          Address, 'us\u0117r@example.com', '')

    def test_high_unicode_email_domain_raises_exception(self):
        self.assertRaises(InvalidEmailAddressError,
                          Address, 'user@\u0117xample.com', '')

    def test_local_part_differs_only_by_case(self):
        with self.assertRaises(ExistingAddressError) as cm:
            self._usermgr.create_address('fperson@example.com')
        self.assertEqual(cm.exception.address, 'FPERSON@example.com')

    def test_domain_part_differs_only_by_case(self):
        with self.assertRaises(ExistingAddressError) as cm:
            self._usermgr.create_address('fperson@EXAMPLE.COM')
        self.assertEqual(cm.exception.address, 'FPERSON@example.com')

    def test_mixed_case_exact_match(self):
        with self.assertRaises(ExistingAddressError) as cm:
            self._usermgr.create_address('FPERSON@example.com')
        self.assertEqual(cm.exception.address, 'FPERSON@example.com')
