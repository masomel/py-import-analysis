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

"""Various test helpers."""

import os
import sys
import time
import uuid
import shutil
import signal
import socket
import logging
import smtplib
import datetime
import threading

from contextlib import contextmanager, suppress
from email import message_from_string
from lazr.config import as_timedelta
from mailman.bin.master import Loop as Master
from mailman.config import config
from mailman.database.transaction import transaction
from mailman.email.message import Message
from mailman.interfaces.member import MemberRole
from mailman.interfaces.messages import IMessageStore
from mailman.interfaces.styles import IStyleManager
from mailman.interfaces.usermanager import IUserManager
from mailman.runners.digest import DigestRunner
from mailman.utilities.mailbox import Mailbox
from public import public
from requests import request
from unittest import mock
from urllib.error import HTTPError
from zope import event
from zope.component import getUtility


NL = '\n'


@public
def make_testable_runner(runner_class, name=None, predicate=None):
    """Create a runner that runs until its queue is empty.

    :param runner_class: The runner class.
    :type runner_class: class
    :param name: Optional queue name; if not given, it is calculated from the
        class name.
    :type name: string or None
    :param predicate: Optional alternative predicate for deciding when to stop
        the runner.  When None (the default) it stops when the queue is empty.
    :type predicate: callable that gets one argument, the queue runner.
    :return: A runner instance.
    """
    if name is None:
        assert runner_class.__name__.endswith('Runner'), (
            'Unparseable runner class name: %s' % runner_class.__name__)
        name = runner_class.__name__[:-6].lower()

    class EmptyingRunner(runner_class):
        """Stop processing when the queue is empty."""

        def __init__(self, *args, **kws):
            super().__init__(*args, **kws)
            # We know it's an EmptyingRunner, so really we want to see the
            # super class in the log files.
            self.__class__.__name__ = runner_class.__name__

        def _do_periodic(self):
            """Stop when the queue is empty."""
            if predicate is None:
                self._stop = (len(self.switchboard.files) == 0)
            else:
                self._stop = predicate(self)

    return EmptyingRunner(name)


class _Bag:
    def __init__(self, **kws):
        for key, value in kws.items():
            setattr(self, key, value)


@public
def get_queue_messages(queue_name, sort_on=None, expected_count=None):
    """Return and clear all the messages in the given queue.

    :param queue_name: A string naming a queue.
    :param sort_on: The message header to sort on.  If None (the default),
        no sorting is performed.
    :param expected_count: If given and there aren't exactly this number of
        messages in the queue, raise an AssertionError.
    :return: A list of 2-tuples where each item contains the message and
        message metadata.
    """
    queue = config.switchboards[queue_name]
    messages = []
    for filebase in queue.files:
        msg, msgdata = queue.dequeue(filebase)
        messages.append(_Bag(msg=msg, msgdata=msgdata))
        queue.finish(filebase)
    if expected_count is not None:
        if len(messages) != expected_count:
            for item in messages:
                print(item.msg, file=sys.stderr)
            raise AssertionError('Wanted {}, got {}'.format(
                expected_count, len(messages)))
    if sort_on is not None:
        messages.sort(key=lambda item: str(item.msg[sort_on]))
    return messages


@public
def digest_mbox(mlist):
    """The mailing list's pending digest as a mailbox.

    :param mlist: The mailing list.
    :return: The mailing list's pending digest as a mailbox.
    """
    path = os.path.join(mlist.data_path, 'digest.mmdf')
    return Mailbox(path)


# Remember, Master is mailman.bin.master.Loop.
@public
class TestableMaster(Master):
    """A testable master loop watcher."""

    def __init__(self, start_check=None):
        """Create a testable master loop watcher.

        :param start_check: Optional callable used to check whether everything
            is running as the test expects.  Called in `loop()` in the
            subthread before the event is set.  The callback should block
            until the pass condition is set.
        :type start_check: Callable taking no arguments, returning nothing.
        """
        super().__init__(restartable=False, config_file=config.filename)
        self.start_check = start_check
        self.event = threading.Event()
        self.thread = threading.Thread(target=self.loop)
        self.thread.daemon = True
        self._started_kids = None

    def _pause(self):
        """See `Master`."""
        # No-op this because the tests generally do not signal the master,
        # which would mean the signal.pause() never exits.
        pass

    def start(self, *runners):
        """Start the master."""
        self.start_runners(runners)
        self.thread.start()
        # Wait until all the children are definitely started.
        self.event.wait()

    def stop(self):
        """Stop the master by killing all the children."""
        for pid in self.runner_pids:
            os.kill(pid, signal.SIGTERM)
        self.cleanup()
        self.thread.join()

    def loop(self):
        """Wait until all the runners are actually running before looping."""
        starting_kids = set(self._kids)
        while starting_kids:
            for pid in self._kids:
                # Ignore the exception which gets raised when the child has
                # not yet started.
                with suppress(ProcessLookupError):
                    os.kill(pid, 0)
                    starting_kids.remove(pid)
        # Keeping a copy of all the started child processes for use by the
        # testing environment, even after all have exited.
        self._started_kids = set(self._kids)
        # If there are extra conditions to check, do it now.
        if self.start_check is not None:
            self.start_check()
        # Let the blocking thread know everything's running.
        self.event.set()
        super().loop()

    @property
    def runner_pids(self):
        """The pids of all the child runner processes."""
        yield from self._started_kids


class LMTP(smtplib.SMTP):
    """Like a normal SMTP client, but for LMTP."""
    def lhlo(self, name=''):
        self.putcmd('lhlo', name or self.local_hostname)
        code, msg = self.getreply()
        self.helo_resp = msg
        return code, msg


@public
def get_lmtp_client(quiet=False):
    """Return a connected LMTP client."""
    # It's possible the process has started but is not yet accepting
    # connections.  Wait a little while.
    lmtp = LMTP()
    # lmtp.debuglevel = 1
    until = datetime.datetime.now() + as_timedelta(config.devmode.wait)
    while datetime.datetime.now() < until:
        try:
            response = lmtp.connect(
                config.mta.lmtp_host, int(config.mta.lmtp_port))
            if not quiet:
                print(response)
            return lmtp
        except ConnectionRefusedError:
            time.sleep(0.1)
    else:
        raise RuntimeError('Connection refused')


@public
def get_nntp_server(cleanups):
    """Create and start an NNTP server mock.

    This can be used to retrieve the posted message for verification.
    """
    patcher = mock.patch('nntplib.NNTP')
    server_class = patcher.start()
    cleanups.callback(patcher.stop)
    nntpd = server_class()
    # A class for more convenient access to the posted message.
    class NNTPProxy:                                              # noqa: E306
        def get_message(self):
            args = nntpd.post.call_args
            return specialized_message_from_string(args[0][0].read())
    return NNTPProxy()


@public
def wait_for_webservice(hostname=None, port=None):
    """Wait for the REST server to start serving requests."""
    hostname = config.webservice.hostname if hostname is None else hostname
    port = int(config.webservice.port) if port is None else port
    until = datetime.datetime.now() + as_timedelta(config.devmode.wait)
    while datetime.datetime.now() < until:
        try:
            socket.socket().connect((hostname, port))
        except ConnectionRefusedError:
            time.sleep(0.1)
        else:
            break
    else:
        raise RuntimeError('Connection refused')


@public
def call_api(url, data=None, method=None, username=None, password=None):
    """'Call a URL with a given HTTP method and return the resulting object.

    The object will have been JSON decoded.

    :param url: The url to open, read, and print.
    :type url: string
    :param data: Data to use to POST to a URL.
    :type data: dict
    :param method: Alternative HTTP method to use.
    :type method: str
    :param username: The HTTP Basic Auth user name.  None means use the value
        from the configuration.
    :type username: str
    :param password: The HTTP Basic Auth password.  None means use the value
        from the configuration.
    :type username: str
    :return: A 2-tuple containing the JSON decoded content (if there is any,
        else None) and the response object.
    :rtype: 2-tuple of (dict, response)
    :raises HTTPError: when a non-2xx return code is received.
    """
    if method is None:
        if data is None:
            method = 'GET'
        else:
            method = 'POST'
    method = method.upper()
    basic_auth = (
        (config.webservice.admin_user if username is None else username),
        (config.webservice.admin_pass if password is None else password))
    response = request(method, url, data=data, auth=basic_auth)
    # For backward compatibility with existing doctests, turn non-2xx response
    # codes into a urllib.error exceptions.
    if response.status_code // 100 != 2:
        raise HTTPError(
            url, response.status_code, response.text, response, None)
    if len(response.content) == 0:
        return None, response
    return response.json(), response


@public
@contextmanager
def event_subscribers(*subscribers):
    """Temporarily extend the Zope event subscribers list.

    :param subscribers: A sequence of event subscribers.
    :type subscribers: sequence of callables, each receiving one argument, the
        event.
    """
    old_subscribers = event.subscribers[:]
    event.subscribers.extend(subscribers)
    try:
        yield
    finally:
        event.subscribers[:] = old_subscribers


@public
class configuration:
    """A decorator/context manager for temporarily setting configurations."""

    def __init__(self, section, **kws):
        self._section = section
        # Most tests don't care about the name given to the temporary
        # configuration.  Usually we'll just craft a random one, but some
        # tests do care, so give them a hook to set it.
        if '_configname' in kws:
            self._uuid = kws.pop('_configname')
        else:
            self._uuid = uuid.uuid4().hex
        self._values = kws.copy()

    def _apply(self):
        lines = ['[{0}]'.format(self._section)]
        for key, value in self._values.items():
            lines.append('{0}: {1}'.format(key, value))
        config.push(self._uuid, NL.join(lines))

    def _remove(self):
        config.pop(self._uuid)

    def __enter__(self):
        self._apply()

    def __exit__(self, *exc_info):
        self._remove()
        # Do not suppress exceptions.
        return False

    def __call__(self, func):
        def wrapper(*args, **kws):
            self._apply()
            try:
                return func(*args, **kws)
            finally:
                self._remove()
        return wrapper


@public
@contextmanager
def temporary_db(db):
    real_db = config.db
    config.db = db
    try:
        yield
    finally:
        config.db = real_db


@public
class chdir:
    """A context manager for temporary directory changing."""
    def __init__(self, directory):
        self._curdir = None
        self._directory = directory

    def __enter__(self):
        self._curdir = os.getcwd()
        os.chdir(self._directory)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self._curdir)
        # Don't suppress exceptions.
        return False


@public
def subscribe(mlist, first_name, role=MemberRole.member, email=None):
    """Helper for subscribing a sample person to a mailing list.

    Returns the newly created member object.
    """
    user_manager = getUtility(IUserManager)
    email = ('{}person@example.com'.format(first_name[0].lower())
             if email is None else email)
    full_name = '{} Person'.format(first_name)
    with transaction():
        person = user_manager.get_user(email)
        if person is None:
            address = user_manager.get_address(email)
            if address is None:
                person = user_manager.create_user(email, full_name)
                subscription_address = list(person.addresses)[0]
            else:
                subscription_address = address
        else:
            subscription_address = list(person.addresses)[0]
        mlist.subscribe(subscription_address, role)
        roster = mlist.get_roster(role)
        return roster.get_member(email)


@public
def reset_the_world():
    """Reset everything:

    * Clear out the database
    * Remove all residual queue and digest files
    * Clear the message store
    * Reset the global style manager

    This should be as thorough a reset of the system as necessary to keep
    tests isolated.
    """
    # Reset the database between tests.
    config.db._reset()
    # Remove any digest files and members.txt file (for the file-recips
    # handler) in the lists' data directories.
    for dirpath, dirnames, filenames in os.walk(config.LIST_DATA_DIR):
        for filename in filenames:
            if filename.endswith('.mmdf') or filename == 'members.txt':
                os.remove(os.path.join(dirpath, filename))
    # Remove all residual queue files.
    for dirpath, dirnames, filenames in os.walk(config.QUEUE_DIR):
        for filename in filenames:
            os.remove(os.path.join(dirpath, filename))
    # Clear out messages in the message store.
    message_store = getUtility(IMessageStore)
    with transaction():
        for message in message_store.messages:
            message_store.delete_message(message['message-id'])
    # Delete any other residual messages.
    for dirpath, dirnames, filenames in os.walk(config.MESSAGES_DIR):
        for filename in filenames:
            os.remove(os.path.join(dirpath, filename))
        shutil.rmtree(dirpath)
    # Remove all the cache subdirectories, recursively.
    for dirname in os.listdir(config.CACHE_DIR):
        shutil.rmtree(os.path.join(config.CACHE_DIR, dirname))
    # Reset the global style manager.
    getUtility(IStyleManager).populate()
    # Remove all dynamic header-match rules.
    config.chains['header-match'].flush()
    # Remove cached organizational domain suffix file.
    from mailman.rules.dmarc import LOCAL_FILE_NAME
    suffix_file = os.path.join(config.VAR_DIR, LOCAL_FILE_NAME)
    with suppress(FileNotFoundError):
        os.remove(suffix_file)


@public
def specialized_message_from_string(unicode_text):
    """Parse text into a message object.

    This is specialized in the sense that an instance of Mailman's own Message
    object is returned, and this message object has an attribute
    `original_size` which is the pre-calculated size in bytes of the message's
    text representation.

    Also, the text must be ASCII-only unicode.
    """
    # This mimic what Switchboard.dequeue() does when parsing a message from
    # text into a Message instance.
    original_size = len(unicode_text)
    message = message_from_string(unicode_text, Message)
    message.original_size = original_size
    return message


@public
class LogFileMark:
    def __init__(self, log_name):
        self._log = logging.getLogger(log_name)
        self._filename = self._log.handlers[0].filename
        self._filepos = os.stat(self._filename).st_size

    def readline(self):
        with open(self._filename) as fp:
            fp.seek(self._filepos)
            return fp.readline()

    def read(self):
        with open(self._filename) as fp:
            fp.seek(self._filepos)
            return fp.read()


@public
def make_digest_messages(mlist, msg=None):
    if msg is None:
        msg = specialized_message_from_string("""\
From: anne@example.org
To: {listname}
Message-ID: <testing>

message triggering a digest
""".format(listname=mlist.fqdn_listname))
    mbox_path = os.path.join(mlist.data_path, 'digest.mmdf')
    config.handlers['to-digest'].process(mlist, msg, {})
    config.switchboards['digest'].enqueue(
        msg,
        listname=mlist.fqdn_listname,
        digest_path=mbox_path,
        volume=1, digest_number=1)
    runner = make_testable_runner(DigestRunner, 'digest')
    runner.run()


@public
def set_preferred(user):
    # Avoid circular imports.
    from mailman.utilities.datetime import now
    preferred = list(user.addresses)[0]
    preferred.verified_on = now()
    user.preferred_address = preferred
    return preferred


@public
@contextmanager
def hackenv(envar, new_value):
    """Hack the environment temporarily, then reset it."""
    old_value = os.getenv(envar)
    if new_value is None:
        if envar in os.environ:
            del os.environ[envar]
    else:
        os.environ[envar] = new_value
    try:
        yield
    finally:
        if old_value is None:
            if envar in os.environ:
                del os.environ[envar]
        else:
            os.environ[envar] = old_value


def nose2_start_test_run_callback(plugin):
    from mailman.testing.layers import ConfigLayer, MockAndMonkeyLayer
    MockAndMonkeyLayer.testing_mode = True
    if (plugin.stderr or
            len(os.environ.get('MM_VERBOSE_TESTLOG', '').strip()) > 0):
        ConfigLayer.stderr = True
