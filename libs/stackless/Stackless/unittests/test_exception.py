from __future__ import absolute_import
import unittest

from support import test_main  # @UnusedImport
from support import StacklessTestCase


class TestException(StacklessTestCase):
    def testTaskletExitCode(self):
        # Tasklet exit was defined as the wrong kind of exception.
        # When its code attribute was accessed the runtime would
        # crash.  This has been fixed.
        exc = TaskletExit()
        exc.code


if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        sys.argv.append('-v')
    unittest.main()
