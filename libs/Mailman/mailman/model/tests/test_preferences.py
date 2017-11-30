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

"""Test preferences."""

import unittest

from mailman.interfaces.languages import ILanguageManager
from mailman.interfaces.member import DeliveryMode, DeliveryStatus
from mailman.interfaces.preferences import IPreferences
from mailman.model.preferences import Preferences
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility
from zope.interface import Attribute
from zope.interface.interface import Method


class TestPreferences(unittest.TestCase):
    """Test preferences."""

    layer = ConfigLayer

    def test_absorb_all_attributes(self):
        # Test that all attributes in the IPreferences interface are properly
        # absorbed, and that none are missed.
        attributes = []
        for name in IPreferences.names():
            attribute = IPreferences.getDescriptionFor(name)
            if (not isinstance(attribute, Method)
                    and isinstance(attribute, Attribute)):   # noqa: W503
                attributes.append(name)
        values = {
            'acknowledge_posts': True,
            'hide_address': True,
            'preferred_language': getUtility(ILanguageManager)['fr'],
            'receive_list_copy': True,
            'receive_own_postings': True,
            'delivery_mode': DeliveryMode.mime_digests,
            'delivery_status': DeliveryStatus.by_user,
            }
        # If this fails, the IPreferences interface has been mutated.  Be sure
        # to update this test!
        self.assertEqual(sorted(attributes), sorted(values))
        preferences_1 = Preferences()
        preferences_2 = Preferences()
        for name, value in values.items():
            setattr(preferences_1, name, value)
        preferences_2.absorb(preferences_1)
        for name, value in values.items():
            self.assertEqual(getattr(preferences_2, name), value)

    def test_absorb_overwrite(self):
        # Only overwrite the preference if it is unset in the absorber.
        preferences_1 = Preferences()
        preferences_2 = Preferences()
        preferences_1.acknowledge_posts = False
        preferences_2.acknowledge_posts = True
        preferences_1.hide_address = True
        preferences_2.receive_list_copy = True
        # Ensure that our preconditions are met.
        self.assertIsNotNone(preferences_1.acknowledge_posts)
        self.assertIsNotNone(preferences_2.acknowledge_posts)
        self.assertIsNotNone(preferences_1.hide_address)
        self.assertIsNone(preferences_2.hide_address)
        self.assertIsNone(preferences_1.receive_list_copy)
        self.assertIsNotNone(preferences_2.receive_list_copy)
        # Do the absorb.
        preferences_1.absorb(preferences_2)
        # This attribute is set in both preferences, so it wasn't absorbed.
        self.assertFalse(preferences_1.acknowledge_posts)
        # This attribute is only set in the first preferences so it also
        # wasn't absorbed.
        self.assertTrue(preferences_1.hide_address)
        # This attribute is only set in the second preferences, so it was
        # absorbed.
        self.assertTrue(preferences_1.receive_list_copy)

    def test_type_error(self):
        preferences = Preferences()
        self.assertRaises(TypeError, preferences.absorb, None)
