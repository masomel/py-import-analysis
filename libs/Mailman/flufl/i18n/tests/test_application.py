"""Additional coverage/unittest for the Application class."""

import unittest
import flufl.i18n.testing.messages

from flufl.i18n import Application, PackageStrategy


class TestApplication(unittest.TestCase):
    def test_application_name(self):
        strategy = PackageStrategy('flufl', flufl.i18n.testing.messages)
        application = Application(strategy)
        self.assertEqual(application.name, 'flufl')
