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

"""Test the workflow model."""

import unittest

from mailman.interfaces.workflow import IWorkflowStateManager
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestWorkflow(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._manager = getUtility(IWorkflowStateManager)

    def test_save_restore_workflow(self):
        # Save and restore a workflow.
        token = 'bee'
        step = 'cat'
        data = 'dog'
        self._manager.save(token, step, data)
        state = self._manager.restore(token)
        self.assertEqual(state.token, token)
        self.assertEqual(state.step, step)
        self.assertEqual(state.data, data)

    def test_save_restore_workflow_without_step(self):
        # Save and restore a workflow that contains no step.
        token = 'bee'
        data = 'dog'
        self._manager.save(token, data=data)
        state = self._manager.restore(token)
        self.assertEqual(state.token, token)
        self.assertIsNone(state.step)
        self.assertEqual(state.data, data)

    def test_save_restore_workflow_without_data(self):
        # Save and restore a workflow that contains no data.
        token = 'bee'
        step = 'cat'
        self._manager.save(token, step)
        state = self._manager.restore(token)
        self.assertEqual(state.token, token)
        self.assertEqual(state.step, step)
        self.assertIsNone(state.data)

    def test_save_restore_workflow_without_step_or_data(self):
        # Save and restore a workflow that contains no step or data.
        token = 'bee'
        self._manager.save(token)
        state = self._manager.restore(token)
        self.assertEqual(state.token, token)
        self.assertIsNone(state.step)
        self.assertIsNone(state.data)

    def test_restore_workflow_with_no_matching_token(self):
        # Try to restore a workflow that has no matching token in the database.
        token = 'bee'
        self._manager.save(token)
        state = self._manager.restore('fly')
        self.assertIsNone(state)

    def test_restore_removes_record(self):
        token = 'bee'
        self.assertEqual(self._manager.count, 0)
        self._manager.save(token)
        self.assertEqual(self._manager.count, 1)
        self._manager.restore(token)
        self.assertEqual(self._manager.count, 0)

    def test_save_after_restore(self):
        token = 'bee'
        self.assertEqual(self._manager.count, 0)
        self._manager.save(token)
        self.assertEqual(self._manager.count, 1)
        self._manager.restore(token)
        self.assertEqual(self._manager.count, 0)
        self._manager.save(token)
        self.assertEqual(self._manager.count, 1)

    def test_discard(self):
        # Discard some workflow state.  This is use by
        # ISubscriptionManager.discard().
        self._manager.save('token1', 'one')
        self._manager.save('token2', 'two')
        self._manager.save('token3', 'three')
        self._manager.save('token4', 'four')
        self.assertEqual(self._manager.count, 4)
        self._manager.discard('token2')
        self.assertEqual(self._manager.count, 3)
        state = self._manager.restore('token1')
        self.assertEqual(state.step, 'one')
        state = self._manager.restore('token2')
        self.assertIsNone(state)
        state = self._manager.restore('token3')
        self.assertEqual(state.step, 'three')
        state = self._manager.restore('token4')
        self.assertEqual(state.step, 'four')

    def test_discard_missing_workflow(self):
        self._manager.discard('bogus-token')
        self.assertEqual(self._manager.count, 0)
