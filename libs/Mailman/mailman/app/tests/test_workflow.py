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

"""App-level workflow tests."""

import json
import unittest

from mailman.app.workflow import Workflow
from mailman.interfaces.workflow import IWorkflowStateManager
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class MyWorkflow(Workflow):
    INITIAL_STATE = 'first'
    SAVE_ATTRIBUTES = ('ant', 'bee', 'cat')

    def __init__(self):
        super().__init__()
        self.token = 'test-workflow'
        self.ant = 1
        self.bee = 2
        self.cat = 3
        self.dog = 4

    def _step_first(self):
        self.push('second')
        return 'one'

    def _step_second(self):
        self.push('third')
        return 'two'

    def _step_third(self):
        return 'three'


class DependentWorkflow(MyWorkflow):
    SAVE_ATTRIBUTES = ('ant', 'bee', 'cat', 'elf')

    def __init__(self):
        super().__init__()
        self._elf = 5

    @property
    def elf(self):
        return self._elf

    @elf.setter
    def elf(self, value):
        # This attribute depends on other attributes.
        assert self.ant is not None
        assert self.bee is not None
        assert self.cat is not None
        self._elf = value


class TestWorkflow(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._workflow = iter(MyWorkflow())

    def test_basic_workflow(self):
        # The work flows from one state to the next.
        results = list(self._workflow)
        self.assertEqual(results, ['one', 'two', 'three'])

    def test_partial_workflow(self):
        # You don't have to flow through every step.
        results = next(self._workflow)
        self.assertEqual(results, 'one')

    def test_exhaust_workflow(self):
        # Manually flow through a few steps, then consume the whole thing.
        results = [next(self._workflow)]
        results.extend(self._workflow)
        self.assertEqual(results, ['one', 'two', 'three'])

    def test_save_and_restore_workflow(self):
        # Without running any steps, save and restore the workflow.  Then
        # consume the restored workflow.
        self._workflow.save()
        new_workflow = MyWorkflow()
        new_workflow.restore()
        results = list(new_workflow)
        self.assertEqual(results, ['one', 'two', 'three'])

    def test_save_and_restore_partial_workflow(self):
        # After running a few steps, save and restore the workflow.  Then
        # consume the restored workflow.
        next(self._workflow)
        self._workflow.save()
        new_workflow = MyWorkflow()
        new_workflow.restore()
        results = list(new_workflow)
        self.assertEqual(results, ['two', 'three'])

    def test_save_and_restore_exhausted_workflow(self):
        # After consuming the entire workflow, save and restore it.
        list(self._workflow)
        self._workflow.save()
        new_workflow = MyWorkflow()
        new_workflow.restore()
        results = list(new_workflow)
        self.assertEqual(len(results), 0)

    def test_save_and_restore_attributes(self):
        # Saved attributes are restored.
        self._workflow.ant = 9
        self._workflow.bee = 8
        self._workflow.cat = 7
        # Don't save .dog.
        self._workflow.save()
        new_workflow = MyWorkflow()
        new_workflow.restore()
        self.assertEqual(new_workflow.ant, 9)
        self.assertEqual(new_workflow.bee, 8)
        self.assertEqual(new_workflow.cat, 7)
        self.assertEqual(new_workflow.dog, 4)

    def test_save_and_restore_dependant_attributes(self):
        # Attributes must be restored in the order they are declared in
        # SAVE_ATTRIBUTES.
        workflow = iter(DependentWorkflow())
        workflow.elf = 6
        workflow.save()
        new_workflow = DependentWorkflow()
        # The elf attribute must be restored last, set triggering values for
        # attributes it depends on.
        new_workflow.ant = new_workflow.bee = new_workflow.cat = None
        new_workflow.restore()
        self.assertEqual(new_workflow.elf, 6)

    def test_save_and_restore_obsolete_attributes(self):
        # Obsolete saved attributes are ignored.
        state_manager = getUtility(IWorkflowStateManager)
        # Save the state of an old version of the workflow that would not have
        # the cat attribute.
        state_manager.save(
            self._workflow.token, 'first',
            json.dumps({'ant': 1, 'bee': 2}))
        # Restore in the current version that needs the cat attribute.
        new_workflow = MyWorkflow()
        try:
            new_workflow.restore()
        except KeyError:
            self.fail('Restore does not handle obsolete attributes')
        # Restoring must not raise an exception, the default value is kept.
        self.assertEqual(new_workflow.cat, 3)

    def test_run_thru(self):
        # Run all steps through the given one.
        results = self._workflow.run_thru('second')
        self.assertEqual(results, ['one', 'two'])

    def test_run_thru_completes(self):
        results = self._workflow.run_thru('all of them')
        self.assertEqual(results, ['one', 'two', 'three'])

    def test_run_until(self):
        # Run until (but not including) the given step.
        results = self._workflow.run_until('second')
        self.assertEqual(results, ['one'])

    def test_run_until_completes(self):
        results = self._workflow.run_until('all of them')
        self.assertEqual(results, ['one', 'two', 'three'])
