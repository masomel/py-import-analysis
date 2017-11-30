# Copyright (C) 2007-2017 by the Free Software Foundation, Inc.
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

"""Interface for runners."""

from public import public
from zope.interface import Attribute, Interface


@public
class RunnerCrashEvent:
    """Triggered when a runner encounters an exception in _dispose()."""

    def __init__(self, runner, mlist, msg, metadata, error):
        self.runner = runner
        self.mailing_list = mlist
        self.message = msg
        self.metadata = metadata
        self.error = error


@public
class RunnerInterrupt(Exception):
    """A runner received a system call interrupting signal.

    PEP 475 automatically, and at the C layer, retries system calls such as
    time.sleep().  This can mean runners with long sleeps in their _snooze()
    method won't actually exit.  This exception is always raised in Mailman's
    runner signal handlers to prevent this behavior.  Runners that implement
    their own .run() method must be prepared to handle this, usually by
    ignoring it.
    """


@public
class IRunner(Interface):
    """The runner."""

    def run():
        """Start the runner."""

    def stop():
        """Stop the runner on the next iteration through the loop."""

    is_queue_runner = Attribute("""\
        A boolean variable describing whether the runner is a queue runner.
        """)

    queue_directory = Attribute(
        'The queue directory.  Overridden in subclasses.')

    sleep_time = Attribute("""\
        The number of seconds this runner will sleep between iterations
        through the main loop.
        """)

    def set_signals():
        """Set up the signal handlers necessary to control the runner.

        The runner should catch the following signals:
        - SIGTERM and SIGINT: treated exactly the same, they cause the runner
          to exit with no restart from the master.
        - SIGUSR1: Also causes the runner to exit, but the master watcher will
          retart it.
        - SIGHUP: Re-open the log files.
        """

    def _one_iteration():
        """The work done in one iteration of the main loop.

        Can be overridden by subclasses.

        :return: The number of files still left to process.
        :rtype: int
        """

    def _process_one_file(msg, msgdata):
        """Process one queue file.

        :param msg: The message object.
        :type msg: `email.message.Message`
        :param msgdata: The message metadata.
        :type msgdata: dict
        """

    def _clean_up():
        """Clean up upon exit from the main processing loop.

        Called when the runner's main loop is stopped, this should perform any
        necessary resource deallocation.
        """

    def _dispose(mlist, msg, msgdata):
        """Dispose of a single message destined for a mailing list.

        Called for each message that the runner is responsible for, this is
        the primary overridable method for processing each message.
        Subclasses, must provide implementation for this method.

        :param mlist: The mailing list this message is destined for.
        :type mlist: `IMailingList`
        :param msg: The message being processed.
        :type msg: `email.message.Message`
        :param msgdata: The message metadata.
        :type msgdata: dict
        :return: True if the message should continue to be queued, False if
            the message should be deleted automatically.
        :rtype: bool
        """

    def _do_periodic():
        """Do some arbitrary periodic processing.

        Called every once in a while both from the runner's main loop, and
        from the runner's hash slice processing loop.  You can do whatever
        special periodic processing you want here.
        """

    def _snooze(filecnt):
        """Sleep for a little while.

        :param filecnt: The number of messages in the queue the last time
            through.  Runners can decide to continue to do work, or sleep for
            a while based on this value.  By default, the base runner only
            snoozes when there was nothing to do last time around.
        :type filecnt: int
        """

    def _short_circuit():
        """Should processing be short-circuited?

        :return: True if the file processing loop should exit before it's
            finished processing each message in the current slice of hash
            space.  False tells _one_iteration() to continue processing until
            the current snapshot of hash space is exhausted.
        :rtype: bool
        """
