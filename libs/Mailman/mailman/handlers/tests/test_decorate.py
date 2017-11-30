# Copyright (C) 2014-2017 by the Free Software Foundation, Inc.
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

"""Test the decorate handler."""

import os
import unittest

from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.handlers import decorate
from mailman.interfaces.archiver import IArchiver
from mailman.interfaces.template import ITemplateManager
from mailman.testing.helpers import (
    LogFileMark, specialized_message_from_string as mfs)
from mailman.testing.layers import ConfigLayer
from tempfile import TemporaryDirectory
from zope.component import getUtility
from zope.interface import implementer


@implementer(IArchiver)
class TestArchiver:
    """A test archiver"""

    name = 'testarchiver'
    is_enabled = False

    @staticmethod
    def permalink(mlist, msg):
        return 'http://example.com/link_to_message'


@implementer(IArchiver)
class BrokenArchiver:
    name = 'broken'
    is_enabled = True

    @staticmethod
    def permalink(mlist, msg):
        raise RuntimeError('Cannot get permalink')


class TestDecorate(unittest.TestCase):
    """Test the cook_headers handler."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._msg = mfs("""\
To: ant@example.com
From: aperson@example.com
Message-ID: <alpha>
Content-Type: text/plain;

This is a test message.
""")
        temporary_dir = TemporaryDirectory()
        self.addCleanup(temporary_dir.cleanup)
        template_dir = temporary_dir.name
        config.push('archiver', """\
        [paths.testing]
        template_dir: {}
        [archiver.testarchiver]
        class: mailman.handlers.tests.test_decorate.TestArchiver
        enable: yes
        """.format(template_dir))
        self.addCleanup(config.pop, 'archiver')

    def test_decorate_footer_with_archive_url(self):
        site_dir = os.path.join(config.TEMPLATE_DIR, 'site', 'en')
        os.makedirs(site_dir)
        footer_path = os.path.join(site_dir, 'myfooter.txt')
        with open(footer_path, 'w', encoding='utf-8') as fp:
            print('${testarchiver_url}', file=fp)
        getUtility(ITemplateManager).set(
            'list:member:regular:footer', None, 'mailman:///myfooter.txt')
        self._mlist.preferred_language = 'en'
        decorate.process(self._mlist, self._msg, {})
        self.assertIn('http://example.com/link_to_message',
                      self._msg.as_string())

    def test_list_id_allowed_in_template_uri(self):
        # Issue #196 - allow the list_id in the template uri expansion.
        list_dir = os.path.join(
            config.TEMPLATE_DIR, 'lists', 'ant.example.com', 'en')
        os.makedirs(list_dir)
        footer_path = os.path.join(list_dir, 'myfooter.txt')
        with open(footer_path, 'w', encoding='utf-8') as fp:
            print('${testarchiver_url}', file=fp)
        getUtility(ITemplateManager).set(
            'list:member:regular:footer', self._mlist.list_id,
            'mailman:///${list_id}/myfooter.txt')
        self._mlist.preferred_language = 'en'
        decorate.process(self._mlist, self._msg, {})
        self.assertIn('http://example.com/link_to_message',
                      self._msg.as_string())

    def test_list_id_and_language_code_allowed_in_template_uri(self):
        # Issue #196 - allow the list_id in the template uri expansion.
        list_dir = os.path.join(
            config.TEMPLATE_DIR, 'lists', 'ant.example.com', 'it')
        os.makedirs(list_dir)
        footer_path = os.path.join(list_dir, 'myfooter.txt')
        with open(footer_path, 'w', encoding='utf-8') as fp:
            print('${testarchiver_url}', file=fp)
        getUtility(ITemplateManager).set(
            'list:member:regular:footer', self._mlist.list_id,
            'mailman:///${list_id}/${language}/myfooter.txt')
        self._mlist.preferred_language = 'it'
        decorate.process(self._mlist, self._msg, {})
        self.assertIn('http://example.com/link_to_message',
                      self._msg.as_string())


class TestBrokenPermalink(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('ant@example.com')
        self._msg = mfs("""\
To: ant@example.com
From: aperson@example.com
Message-ID: <alpha>
Content-Type: text/plain;

This is a test message.
""")
        temporary_dir = TemporaryDirectory()
        self.addCleanup(temporary_dir.cleanup)
        template_dir = temporary_dir.name
        config.push('archiver', """\
        [paths.testing]
        template_dir: {}
        [archiver.testarchiver]
        class: mailman.handlers.tests.test_decorate.BrokenArchiver
        enable: yes
        """.format(template_dir))
        self.addCleanup(config.pop, 'archiver')

    def test_broken_permalink(self):
        # GL issue #208 - IArchive messages raise exceptions, breaking the
        # rfc-2369 handler and shunting messages.
        site_dir = os.path.join(config.TEMPLATE_DIR, 'site', 'en')
        os.makedirs(site_dir)
        footer_path = os.path.join(site_dir, 'myfooter.txt')
        with open(footer_path, 'w', encoding='utf-8') as fp:
            print('${broken_url}', file=fp)
        getUtility(ITemplateManager).set(
            'list:member:regular:footer', self._mlist.list_id,
            'mailman:///myfooter.txt')
        self._mlist.preferred_language = 'en'
        mark = LogFileMark('mailman.archiver')
        decorate.process(self._mlist, self._msg, {})
        log_messages = mark.read()
        self.assertNotIn('http:', self._msg.as_string())
        self.assertIn('Exception in "broken" archiver', log_messages)
        self.assertIn('RuntimeError: Cannot get permalink', log_messages)
