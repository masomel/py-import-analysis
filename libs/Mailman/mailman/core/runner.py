# Copyright (C) 2001-2017 by the Free Software Foundation, Inc.
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

"""The process runner base class."""

import time
import signal
import logging
import traceback

from contextlib import suppress
from io import StringIO
from lazr.config import as_boolean, as_timedelta
from mailman.config import config
from mailman.core.i18n import _
from mailman.core.logging import reopen
from mailman.core.switchboard import Switchboard
from mailman.interfaces.languages import ILanguageManager
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.runner import (
    IRunner, RunnerCrashEvent, RunnerInterrupt)
from mailman.utilities.string import expand
from public import public
from zope.component import getUtility
from zope.event import notify
from zope.interface import implementer


dlog = logging.getLogger('mailman.debug')
elog = logging.getLogger('mailman.error')
rlog = logging.getLogger('mailman.runner')


@public
@implementer(IRunner)
class Runner:
    is_queue_runner = True

    def __init__(self, name, slice=None):
        """Create a runner.

        :param slice: The slice number for this runner.  This is passed
            directly to the underlying `ISwitchboard` object.  This is ignored
            for runners that don't manage a queue.
        :type slice: int or None
        """
        # Grab the configuration section.
        self.name = name
        section = getattr(config, 'runner.' + name)
        substitutions = config.paths
        substitutions['name'] = name
        numslices = int(section.instances)
        # Check whether the runner is queue runner or not; non-queue runner
        # should not have queue_directory or switchboard instance.
        if self.is_queue_runner:
            self.queue_directory = expand(section.path, None, substitutions)
            self.switchboard = Switchboard(
                name, self.queue_directory, slice, numslices, True)
        else:
            self.queue_directory = None
            self.switchboard = None
        self.sleep_time = as_timedelta(section.sleep_time)
        # sleep_time is a timedelta; turn it into a float for time.sleep().
        self.sleep_float = (86400 * self.sleep_time.days +
                            self.sleep_time.seconds +
                            self.sleep_time.microseconds / 1.0e6)
        self.max_restarts = int(section.max_restarts)
        self.start = as_boolean(section.start)
        self._stop = False
        self.status = 0

    def __repr__(self):
        return '<{} at {:#x}>'.format(self.__class__.__name__, id(self))

    def signal_handler(self, signum, frame):
        signame = {
            signal.SIGTERM: 'SIGTERM',
            signal.SIGINT: 'SIGINT',
            signal.SIGUSR1: 'SIGUSR1',
            }.get(signum, signum)
        if signum == signal.SIGHUP:
            reopen()
            rlog.info('%s runner caught SIGHUP.  Reopening logs.', self.name)
        elif signum in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
            self.stop()
            self.status = signum
            rlog.info('%s runner caught %s.  Stopping.', self.name, signame)
            # As of Python 3.5, PEP 475 gets in our way.  Runners with long
            # time.sleep()'s in their _snooze() method (e.g. the retry runner)
            # will have their system call implemented time.sleep()
            # automatically retried at the C layer.  The only reliable way to
            # prevent this is to raise an exception in the signal handler.  The
            # standard run() method automatically suppresses this exception,
            # meaning, it's caught and ignored, but effectively breaks the
            # run() loop, which is just what we want.  Runners which implement
            # their own run() method must be prepared to catch
            # RunnerInterrupts, usually also ignoring them.
            raise RunnerInterrupt

    def set_signals(self):
        """See `IRunner`."""
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGUSR1, self.signal_handler)

    def stop(self):
        """See `IRunner`."""
        self._stop = True

    def run(self):
        """See `IRunner`."""
        # Start the main loop for this runner.
        with suppress(KeyboardInterrupt, RunnerInterrupt):
            while True:
                # Once through the loop that processes all the files in the
                # queue directory.
                filecnt = self._one_iteration()
                # Do the periodic work for the subclass.
                self._do_periodic()
                # If the stop flag is set, we're done.
                if self._stop:
                    break
                # Give the runner an opportunity to snooze for a while, but
                # pass it the file count so it can decide whether to do more
                # work now or not.
                self._snooze(filecnt)
        self._clean_up()

    def _one_iteration(self):
        """See `IRunner`."""
        me = self.__class__.__name__
        dlog.debug('[%s] starting oneloop', me)
        # List all the files in our queue directory.  The switchboard is
        # guaranteed to hand us the files in FIFO order.
        files = self.switchboard.files
        for filebase in files:
            dlog.debug('[%s] processing filebase: %s', me, filebase)
            try:
                # Ask the switchboard for the message and metadata objects
                # associated with this queue file.
                msg, msgdata = self.switchboard.dequeue(filebase)
            except Exception as error:
                # This used to just catch email.Errors.MessageParseError, but
                # other problems can occur in message parsing, e.g.
                # ValueError, and exceptions can occur in unpickling too.  We
                # don't want the runner to die, so we just log and skip this
                # entry, but preserve it for analysis.
                self._log(error)
                elog.error('Skipping and preserving unparseable message: %s',
                           filebase)
                self.switchboard.finish(filebase, preserve=True)
                config.db.abort()
                continue
            try:
                dlog.debug('[%s] processing onefile', me)
                self._process_one_file(msg, msgdata)
                dlog.debug('[%s] finishing filebase: %s', me, filebase)
                self.switchboard.finish(filebase)
            except Exception as error:
                # All runners that implement _dispose() must guarantee that
                # exceptions are caught and dealt with properly.  Still, there
                # may be a bug in the infrastructure, and we do not want those
                # to cause messages to be lost.  Any uncaught exceptions will
                # cause the message to be stored in the shunt queue for human
                # intervention.
                self._log(error)
                # Put a marker in the metadata for unshunting.
                msgdata['whichq'] = self.switchboard.name
                # It is possible that shunting can throw an exception, e.g. a
                # permissions problem or a MemoryError due to a really large
                # message.  Try to be graceful.
                try:
                    shunt = config.switchboards['shunt']
                    new_filebase = shunt.enqueue(msg, msgdata)
                    elog.error('SHUNTING: %s', new_filebase)
                    self.switchboard.finish(filebase)
                except Exception as error:
                    # The message wasn't successfully shunted.  Log the
                    # exception and try to preserve the original queue entry
                    # for possible analysis.
                    self._log(error)
                    elog.error(
                        'SHUNTING FAILED, preserving original entry: %s',
                        filebase)
                    self.switchboard.finish(filebase, preserve=True)
                config.db.abort()
            # Other work we want to do each time through the loop.
            dlog.debug('[%s] doing periodic', me)
            self._do_periodic()
            dlog.debug('[%s] committing transaction', me)
            config.db.commit()
            dlog.debug('[%s] checking short circuit', me)
            if self._short_circuit():
                dlog.debug('[%s] short circuiting', me)
                break
        dlog.debug('[%s] ending oneloop: %s', me, len(files))
        return len(files)

    def _process_one_file(self, msg, msgdata):
        """See `IRunner`."""
        # Do some common sanity checking on the message metadata.  It's got to
        # be destined for a particular mailing list.  This switchboard is used
        # to shunt off badly formatted messages.  We don't want to just trash
        # them because they may be fixable with human intervention.  Just get
        # them out of our sight.
        #
        # Find out which mailing list this message is destined for.
        mlist = None
        missing = object()
        # First try to dig out the target list by id.  If there's no list-id
        # in the metadata, fall back to the fqdn list name for backward
        # compatibility.
        list_manager = getUtility(IListManager)
        list_id = msgdata.get('listid', missing)
        fqdn_listname = None
        if list_id is missing:
            fqdn_listname = msgdata.get('listname', missing)
            # XXX Deprecate.
            if fqdn_listname is not missing:
                mlist = list_manager.get(fqdn_listname)
        else:
            mlist = list_manager.get_by_list_id(list_id)
        if mlist is None:
            identifier = (list_id if list_id is not None else fqdn_listname)
            elog.error(
                '%s runner "%s" shunting message for missing list: %s',
                msg['message-id'], self.name, identifier)
            config.switchboards['shunt'].enqueue(msg, msgdata)
            return
        # Now process this message.  We also want to set up the language
        # context for this message.  The context will be the preferred
        # language for the user if the sender is a member of the list, or it
        # will be the list's preferred language.  However, we must take
        # special care to reset the defaults, otherwise subsequent messages
        # may be translated incorrectly.
        if mlist is None:
            language_manager = getUtility(ILanguageManager)
            language = language_manager[config.mailman.default_language]
        elif msg.sender:
            member = mlist.members.get_member(msg.sender)
            language = (member.preferred_language
                        if member is not None
                        else mlist.preferred_language)
        else:
            language = mlist.preferred_language
        with _.using(language.code):
            msgdata['lang'] = language.code
            try:
                keepqueued = self._dispose(mlist, msg, msgdata)
            except Exception as error:
                # Trigger the Zope event and re-raise
                notify(RunnerCrashEvent(self, mlist, msg, msgdata, error))
                raise
        if keepqueued:
            self.switchboard.enqueue(msg, msgdata)

    def _log(self, exc):
        elog.error('Uncaught runner exception: %s', exc)
        s = StringIO()
        traceback.print_exc(file=s)
        elog.error('%s', s.getvalue())

    def _clean_up(self):
        """See `IRunner`."""
        pass

    def _dispose(self, mlist, msg, msgdata):
        """See `IRunner`."""
        raise NotImplementedError

    def _do_periodic(self):
        """See `IRunner`."""
        pass

    def _snooze(self, filecnt):
        """See `IRunner`."""
        if filecnt or self.sleep_float <= 0:
            return
        time.sleep(self.sleep_float)

    def _short_circuit(self):
        """See `IRunner`."""
        return self._stop
