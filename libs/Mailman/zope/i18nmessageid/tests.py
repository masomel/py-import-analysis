##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Message ID tests.
"""
import sys
import unittest

from zope.i18nmessageid import message as messageid

class PyMessageTests(unittest.TestCase):

    _TEST_REAOONLY = True

    def _getTargetClass(self):
        return messageid.pyMessage

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_ctor_defaults(self):
        message = self._makeOne('testing')
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, None)
        self.assertEqual(message.default, None)
        self.assertEqual(message.mapping, None)
        if self._TEST_REAOONLY:
            self.assertTrue(message._readonly)

    def test_ctor_explicit(self):
        mapping = {'key': 'value'}
        message = self._makeOne('testing', 'domain', 'default', mapping)
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, 'domain')
        self.assertEqual(message.default, 'default')
        self.assertEqual(message.mapping, mapping)
        if self._TEST_REAOONLY:
            self.assertTrue(message._readonly)

    def test_ctor_copy(self):
        mapping = {'key': 'value'}
        source = self._makeOne('testing', 'domain', 'default', mapping)
        message = self._makeOne(source)
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, 'domain')
        self.assertEqual(message.default, 'default')
        self.assertEqual(message.mapping, mapping)
        if self._TEST_REAOONLY:
            self.assertTrue(message._readonly)

    def test_ctor_copy_w_overrides(self):
        mapping = {'key': 'value'}
        source = self._makeOne('testing')
        message = self._makeOne(source, 'domain', 'default', mapping)
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, 'domain')
        self.assertEqual(message.default, 'default')
        self.assertEqual(message.mapping, mapping)
        if self._TEST_REAOONLY:
            self.assertTrue(message._readonly)

    def test_domain_immutable(self):
        message = self._makeOne('testing')
        def _try():
            message.domain = 'domain'
        # C version raises AttributeError, Python version TypeError
        self.assertRaises((TypeError, AttributeError), _try)

    def test_default_immutable(self):
        message = self._makeOne('testing')
        def _try():
            message.default = 'default'
        # C version raises AttributeError, Python version TypeError
        self.assertRaises((TypeError, AttributeError), _try)

    def test_mapping_immutable(self):
        mapping = {'key': 'value'}
        message = self._makeOne('testing')
        def _try():
            message.mapping = mapping
        # C version raises AttributeError, Python version TypeError
        self.assertRaises((TypeError, AttributeError), _try)

    def test_unknown_immutable(self):
        message = self._makeOne('testing')
        def _try():
            message.unknown = 'unknown'
        # C version raises AttributeError, Python version TypeError
        self.assertRaises((TypeError, AttributeError), _try)

    def test___reduce__(self):
        mapping = {'key': 'value'}
        source = self._makeOne('testing')
        message = self._makeOne(source, 'domain', 'default', mapping)
        klass, state = message.__reduce__()
        self.assertTrue(klass is self._getTargetClass())
        self.assertEqual(state, ('testing', 'domain', 'default', mapping))

    def test_non_unicode_default(self):
        message = self._makeOne(u'str', default=123)
        self.assertEqual(message.default, 123)

@unittest.skipIf(messageid.Message is messageid.pyMessage,
                 "Duplicate tests")
class MessageTests(PyMessageTests):

    _TEST_REAOONLY = False

    def _getTargetClass(self):
        return messageid.Message

@unittest.skipIf('java' in sys.platform or hasattr(sys, 'pypy_version_info'),
                 "We don't expect the C implementation here")
class OptimizationTests(unittest.TestCase):

    def test_optimizations_available(self):
        self.assertIsNot(messageid.Message, messageid.pyMessage)

class MessageFactoryTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.i18nmessageid.message import MessageFactory
        return MessageFactory

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test___call___defaults(self):
        from zope.i18nmessageid.message import Message
        factory = self._makeOne('domain')
        message = factory('testing')
        self.assertTrue(isinstance(message, Message))
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, 'domain')
        self.assertEqual(message.default, None)
        self.assertEqual(message.mapping, None)

    def test___call___explicit(self):
        from zope.i18nmessageid.message import Message
        mapping = {'key': 'value'}
        factory = self._makeOne('domain')
        message = factory('testing', 'default', mapping)
        self.assertTrue(isinstance(message, Message))
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, 'domain')
        self.assertEqual(message.default, 'default')
        self.assertEqual(message.mapping, mapping)


def test_suite():
    return unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromName(__name__),
    ))
