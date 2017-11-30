from __future__ import absolute_import
import unittest
import weakref

from stackless import *

from support import test_main  # @UnusedImport
from support import StacklessTestCase


class Counter(object):
    ctr = 0

    def __call__(self, *args):
        self.ctr += 1
        return self.ctr

    def get(self):
        return self.ctr


class TestWeakReferences(StacklessTestCase):

    def testSimpleTaskletWeakRef(self):
        counter = Counter()
        t = tasklet(lambda: None)()
        t_ref = weakref.ref(t, counter)
        self.assertEqual(t_ref(), t)
        del t
        # we need to kill it at this point to get collected
        stackless.run()
        self.assertEqual(t_ref(), None)
        self.assertEqual(counter.get(), 1)

    def testSimpleChannelWeakRef(self):
        counter = Counter()
        c = channel()
        c_ref = weakref.ref(c, counter)
        self.assertEqual(c_ref(), c)
        del c
        # we need to kill it at this point to get collected
        stackless.run()
        self.assertEqual(c_ref(), None)
        self.assertEqual(counter.get(), 1)

if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        sys.argv.append('-v')
    unittest.main()
