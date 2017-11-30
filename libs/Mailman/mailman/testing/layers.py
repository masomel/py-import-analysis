# Copyright (C) 2008-2017 by the Free Software Foundation, Inc.
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

"""Mailman test layers."""

# XXX 2012-03-23 BAW: Layers really really suck.  For example, the
# test_owners_get_email() test requires that both the SMTPLayer and LMTPLayer
# be set up, but there's apparently no way to do that and make zope.testing
# happy.  This causes no test failures, but it does cause errors at the end of
# the full test run.  For now, I'll ignore that, but I do want to eventually
# get rid of the layers and use something like testresources or some such.

import os
import sys
import shutil
import logging
import datetime
import tempfile

from lazr.config import as_boolean
from mailman.config import config
from mailman.core import initialize
from mailman.core.initialize import INHIBIT_CONFIG_FILE
from mailman.core.logging import get_handler
from mailman.database.transaction import transaction
from mailman.interfaces.domain import IDomainManager
from mailman.testing.helpers import (
    TestableMaster, get_lmtp_client, reset_the_world, wait_for_webservice)
from mailman.testing.mta import ConnectionCountingController
from mailman.utilities.string import expand
from pkg_resources import resource_string as resource_bytes
from public import public
from textwrap import dedent
from zope.component import getUtility


TEST_TIMEOUT = datetime.timedelta(seconds=5)
NL = '\n'


@public
class MockAndMonkeyLayer:
    """Layer for mocking and monkey patching for testing."""

    # Set this to True to enable predictable datetimes, uids, etc.
    testing_mode = False

    # A registration of all testing factories, for resetting between tests.
    _resets = []

    @classmethod
    def testTearDown(cls):
        for reset in cls._resets:
            reset()

    @classmethod
    def register_reset(cls, reset):
        cls._resets.append(reset)


@public
class ConfigLayer(MockAndMonkeyLayer):
    """Layer for pushing and popping test configurations."""

    var_dir = None
    styles = None

    @classmethod
    def setUp(cls):
        # Set up the basic configuration stuff.  Turn off path creation until
        # we've pushed the testing config.
        config.create_paths = False
        initialize.initialize_1(INHIBIT_CONFIG_FILE)
        assert cls.var_dir is None, 'Layer already set up'
        # Calculate a temporary VAR_DIR directory so that run-time artifacts
        # of the tests won't tread on the installation's data.  This also
        # makes it easier to clean up after the tests are done, and insures
        # isolation of test suite runs.
        cls.var_dir = tempfile.mkdtemp()
        # We need a test configuration both for the foreground process and any
        # child processes that get spawned.  lazr.config would allow us to do
        # it all in a string that gets pushed, and we'll do that for the
        # foreground, but because we may be spawning processes (such as
        # runners) we'll need a file that we can specify to the with the -C
        # option.  Craft the full test configuration string here, push it, and
        # also write it out to a temp file for -C.
        #
        # Create a dummy postfix.cfg file so that the test suite doesn't try
        # to run the actual postmap command, which may not exist anyway.
        postfix_cfg = os.path.join(cls.var_dir, 'postfix.cfg')
        with open(postfix_cfg, 'w') as fp:
            print(dedent("""
            [postfix]
            postmap_command: true
            transport_file_type: hash
            """), file=fp)
        test_config = dedent("""
        [mailman]
        layout: testing
        [paths.testing]
        var_dir: {}
        [devmode]
        testing: yes
        [mta]
        configuration: {}
        """.format(cls.var_dir, postfix_cfg))
        # Read the testing config and push it.
        more = resource_bytes('mailman.testing', 'testing.cfg')
        test_config += more.decode('utf-8')
        config.create_paths = True
        config.push('test config', test_config)
        # Initialize everything else.
        initialize.initialize_2(testing=True)
        initialize.initialize_3()
        # When stderr debugging is enabled, subprocess root loggers should
        # also be more verbose.
        if cls.stderr:
            test_config += dedent("""
            [logging.root]
            level: debug
            """)
        # Enable log message propagation and reset the log paths so that the
        # doctests can check the output.
        for logger_config in config.logger_configs:
            sub_name = logger_config.name.split('.')[-1]
            if sub_name == 'root':
                continue
            logger_name = 'mailman.' + sub_name
            log = logging.getLogger(logger_name)
            log.propagate = cls.stderr
            # Reopen the file to a new path that tests can get at.  Instead of
            # using the configuration file path though, use a path that's
            # specific to the logger so that tests can find expected output
            # more easily.
            path = os.path.join(config.LOG_DIR, sub_name)
            get_handler(sub_name).reopen(path)
            log.setLevel(logging.DEBUG)
            # If stderr debugging is enabled, make sure subprocesses are also
            # more verbose.  In general though, we still don't want SQLAlchemy
            # debugging because it's just too verbose.  Unfortunately, if you
            # do want that level of debugging you currently have to manually
            # modify this conditional.
            if cls.stderr and sub_name != 'database':
                test_config += expand(dedent("""
                [logging.$name]
                propagate: yes
                level: debug
                """), None, dict(name=sub_name, path=path))
        # The root logger will already have a handler, but it's not the right
        # handler.  Remove that and set our own.
        if cls.stderr:
            console = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter(config.logging.root.format,
                                          config.logging.root.datefmt)
            console.setFormatter(formatter)
            root = logging.getLogger()
            del root.handlers[:]
            root.addHandler(console)
        # Write the configuration file for subprocesses and set up the config
        # object to pass that properly on the -C option.
        config_file = os.path.join(cls.var_dir, 'test.cfg')
        with open(config_file, 'w') as fp:
            fp.write(test_config)
            print(file=fp)
        config.filename = config_file

    @classmethod
    def tearDown(cls):
        assert cls.var_dir is not None, 'Layer not set up'
        reset_the_world()
        # Destroy the test database after the tests are done so that there is
        # no data in case the tests are rerun with a database layer like mysql
        # or postgresql which are not deleted in teardown.
        shutil.rmtree(cls.var_dir)
        # Prevent the bit of post-processing on the .pop() that creates
        # directories.  We're basically shutting down everything and we don't
        # need the directories created.  Plus, doing so leaves a var directory
        # turd in the source tree's top-level directory.  We do it this way
        # rather than shutil.rmtree'ing the resulting var directory because
        # it's possible the user created a valid such directory for
        # operational or test purposes.
        config.create_paths = False
        config.pop('test config')
        cls.var_dir = None

    @classmethod
    def testSetUp(cls):
        # Add an example domain.
        with transaction():
            getUtility(IDomainManager).add('example.com', 'An example domain.')

    @classmethod
    def testTearDown(cls):
        reset_the_world()

    # Flag to indicate that loggers should propagate to the console.
    stderr = False

    # The top of our source tree, for tests that care (e.g. hooks.txt).
    root_directory = None

    @classmethod
    def set_root_directory(cls, directory):
        """Set the directory at the root of our source tree.

        zc.recipe.testrunner runs from parts/test/working-directory, but
        that's actually changed over the life of the package.  Some tests
        care, e.g. because they need to find our built-out bin directory.
        Fortunately, buildout can give us this information.  See the
        `buildout.cfg` file for where this method is called.
        """
        cls.root_directory = directory


@public
class SMTPLayer(ConfigLayer):
    """Layer for starting, stopping, and accessing a test SMTP server."""

    smtpd = None

    @classmethod
    def setUp(cls):
        assert cls.smtpd is None, 'Layer already set up'
        host = config.mta.smtp_host
        port = int(config.mta.smtp_port)
        cls.smtpd = ConnectionCountingController(host, port)
        cls.smtpd.start()

    @classmethod
    def tearDown(cls):
        assert cls.smtpd is not None, 'Layer not set up'
        cls.smtpd.clear()
        cls.smtpd.stop()

    @classmethod
    def testSetUp(cls):
        # Make sure we don't call our superclass's testSetUp(), otherwise the
        # example.com domain will get added twice.
        pass

    @classmethod
    def testTearDown(cls):
        cls.smtpd.reset()
        cls.smtpd.clear()


@public
class LMTPLayer(ConfigLayer):
    """Layer for starting, stopping, and accessing a test LMTP server."""

    lmtpd = None

    @staticmethod
    def _wait_for_lmtp_server():
        get_lmtp_client(quiet=True)

    @classmethod
    def setUp(cls):
        assert cls.lmtpd is None, 'Layer already set up'
        cls.lmtpd = TestableMaster(cls._wait_for_lmtp_server)
        cls.lmtpd.start('lmtp')

    @classmethod
    def tearDown(cls):
        assert cls.lmtpd is not None, 'Layer not set up'
        cls.lmtpd.stop()
        cls.lmtpd = None

    @classmethod
    def testSetUp(cls):
        # Make sure we don't call our superclass's testSetUp(), otherwise the
        # example.com domain will get added twice.
        pass


@public
class RESTLayer(SMTPLayer):
    """Layer for starting, stopping, and accessing the test REST layer."""

    server = None

    @classmethod
    def setUp(cls):
        assert cls.server is None, 'Layer already set up'
        cls.server = TestableMaster(wait_for_webservice)
        cls.server.start('rest')

    @classmethod
    def tearDown(cls):
        assert cls.server is not None, 'Layer not set up'
        cls.server.stop()
        cls.server = None


@public
def is_testing():
    """Return a 'testing' flag for use with the predictable factories.

    :return: True when in testing mode.
    :rtype: bool
    """
    return (MockAndMonkeyLayer.testing_mode or
            as_boolean(config.devmode.testing))
