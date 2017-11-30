# Copyright (C) 2015-2017 by the Free Software Foundation, Inc.
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

"""Generic workflow."""

import sys
import json
import logging

from collections import deque
from mailman.interfaces.workflow import IWorkflowStateManager
from public import public
from zope.component import getUtility


COMMASPACE = ', '
log = logging.getLogger('mailman.error')


@public
class Workflow:
    """Generic workflow."""

    SAVE_ATTRIBUTES = ()
    INITIAL_STATE = None

    def __init__(self):
        self.token = None
        self._next = deque()
        self.push(self.INITIAL_STATE)
        self.debug = False
        self._count = 0

    @property
    def name(self):
        return self.__class__.__name__

    def __iter__(self):
        return self

    def push(self, step):
        self._next.append(step)

    def _pop(self):
        name = self._next.popleft()
        step = getattr(self, '_step_{}'.format(name))
        self._count += 1
        if self.debug:                              # pragma: no cover
            print('[{:02d}] -> {}'.format(self._count, name), file=sys.stderr)
        return name, step

    def __next__(self):
        try:
            name, step = self._pop()
            return step()
        except IndexError:
            raise StopIteration
        except:
            log.exception('deque: {}'.format(COMMASPACE.join(self._next)))
            raise

    def run_thru(self, stop_after):
        """Run the state machine through and including the given step.

        :param stop_after: Name of method, sans prefix to run the
            state machine through.  In other words, the state machine runs
            until the named method completes.
        """
        results = []
        while True:
            try:
                name, step = self._pop()
            except (StopIteration, IndexError):
                # We're done.
                break
            results.append(step())
            if name == stop_after:
                break
        return results

    def run_until(self, stop_before):
        """Trun the state machine until (not including) the given step.

        :param stop_before: Name of method, sans prefix that the
            state machine is run until the method is reached.  Unlike
            `run_thru()` the named method is not run.
        """
        results = []
        while True:
            try:
                name, step = self._pop()
            except (StopIteration, IndexError):
                # We're done.
                break
            if name == stop_before:
                # Stop executing, but not before we push the last state back
                # onto the deque.  Otherwise, resuming the state machine would
                # skip this step.
                self._next.appendleft(name)
                break
            results.append(step())
        return results

    def save(self):
        assert self.token, 'Workflow token must be set'
        state_manager = getUtility(IWorkflowStateManager)
        data = {attr: getattr(self, attr) for attr in self.SAVE_ATTRIBUTES}
        # Note: only the next step is saved, not the whole stack.  This is not
        # an issue in practice, since there's never more than a single step in
        # the queue anyway.  If we want to support more than a single step in
        # the queue *and* want to support state saving/restoring, change this
        # method and the restore() method.
        if len(self._next) == 0:
            step = None
        elif len(self._next) == 1:
            step = self._next[0]
        else:
            raise AssertionError(
                "Can't save a workflow state with more than one step "
                "in the queue")
        state_manager.save(self.token, step, json.dumps(data))

    def restore(self):
        state_manager = getUtility(IWorkflowStateManager)
        state = state_manager.restore(self.token)
        if state is None:
            # The token doesn't exist in the database.
            raise LookupError(self.token)
        self._next.clear()
        if state.step:
            self._next.append(state.step)
        data = json.loads(state.data)
        for attr in self.SAVE_ATTRIBUTES:
            try:
                setattr(self, attr, data[attr])
            except KeyError:
                pass
