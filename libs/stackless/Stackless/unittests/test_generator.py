from __future__ import absolute_import
import unittest
import gc
import stackless
import types

from support import test_main  # @UnusedImport
from support import StacklessTestCase


def f():
    yield 1


class TestGarbageCollection(StacklessTestCase):

    def testSimpleLeakage(self):
        leakage = []

        with stackless.atomic():
            gc.collect(2)
            before = frozenset(id(o) for o in gc.get_objects())

            for i in f():
                pass

            gc.collect(2)
            after = gc.get_objects()

        for x in after:
            if x is not before and id(x) not in before:
                leakage.append(x)

        try:
            __in_psyco__  # @UndefinedVariable
            relevant = False
        except NameError:
            relevant = True
        if relevant and len(leakage):
            self.assertTrue(len(leakage) == 0, "Leaked %s" % repr(leakage))


class TestGeneratorWrapper(StacklessTestCase):
    def test_run_wrap_generator(self):
        g = stackless._wrap.generator()
        self.assertIsInstance(g, types.GeneratorType)
        self.assertIsNot(type(g), types.GeneratorType)
        self.assertRaises(StopIteration, next, g)

    def test_wrap_generator_frame_code(self):
        g0 = stackless._wrap.generator()
        g1 = stackless._wrap.generator()
        self.assertIsInstance(g0.gi_frame, types.FrameType)
        self.assertIsInstance(g0.gi_code, types.CodeType)
        self.assertIs(g0.gi_code, g1.gi_code)
        self.assertIsNot(g0.gi_frame, g1.gi_frame)
        self.assertEqual(g0.__name__, "exhausted_generator")

if __name__ == '__main__':
    unittest.main()
