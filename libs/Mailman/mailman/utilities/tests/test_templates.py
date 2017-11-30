# Copyright (C) 2011-2017 by the Free Software Foundation, Inc.
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

"""Testing i18n template search and interpolation."""

import os
import shutil
import tempfile
import unittest

from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.interfaces.languages import ILanguageManager
from mailman.testing.layers import ConfigLayer
from mailman.utilities.i18n import TemplateNotFoundError, find, search
from pkg_resources import resource_filename
from zope.component import getUtility


class TestSearchOrder(unittest.TestCase):
    """Test internal search order for language templates."""

    layer = ConfigLayer

    def setUp(self):
        self.var_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.var_dir)
        config.push('no template dir', """\
        [mailman]
        default_language: fr
        [paths.testing]
        var_dir: {}
        """.format(self.var_dir))
        self.addCleanup(config.pop, 'no template dir')
        self.mlist = create_list('l@example.com')
        self.mlist.preferred_language = 'de'

    def _stripped_search_order(self, template_file,
                               mailing_list=None, language=None):
        # Return the search path order for a given template, possibly using
        # the mailing list and the language as context.  Note that this only
        # returns the search path, and does not check for whether the paths
        # exist or not.
        #
        # Replace the tempdir prefix with a placeholder for more readable and
        # reproducible tests.  Essentially the paths below are rooted at
        # $var_dir, except those files that live within Mailman's source
        # tree.  The former will use /v/ as the root and the latter will use
        # /m/ as the root.
        in_tree = os.path.dirname(resource_filename('mailman', 'templates'))
        raw_search_order = search(template_file, mailing_list, language)
        for path in raw_search_order:
            if path.startswith(self.var_dir):
                path = '/v' + path[len(self.var_dir):]
            elif path.startswith(in_tree):
                path = '/m' + path[len(in_tree):]
            else:
                # This will cause tests to fail, so keep the full bogus
                # pathname for better debugging.
                pass
            yield path

    def test_fully_specified_search_order(self):
        search_order = self._stripped_search_order('foo.txt', self.mlist, 'it')
        # For convenience.
        def nexteq(path):                                        # noqa: E306
            self.assertEqual(next(search_order), path)
        # 1: Use the given language argument
        nexteq('/v/templates/lists/l.example.com/it/foo.txt')
        nexteq('/v/templates/lists/l@example.com/it/foo.txt')
        nexteq('/v/templates/domains/example.com/it/foo.txt')
        nexteq('/v/templates/site/it/foo.txt')
        # 2: Use mlist.preferred_language
        nexteq('/v/templates/lists/l.example.com/de/foo.txt')
        nexteq('/v/templates/lists/l@example.com/de/foo.txt')
        nexteq('/v/templates/domains/example.com/de/foo.txt')
        nexteq('/v/templates/site/de/foo.txt')
        # 3: Use the site's default language
        nexteq('/v/templates/lists/l.example.com/fr/foo.txt')
        nexteq('/v/templates/lists/l@example.com/fr/foo.txt')
        nexteq('/v/templates/domains/example.com/fr/foo.txt')
        nexteq('/v/templates/site/fr/foo.txt')
        # 4: English
        nexteq('/v/templates/lists/l.example.com/en/foo.txt')
        nexteq('/v/templates/lists/l@example.com/en/foo.txt')
        nexteq('/v/templates/domains/example.com/en/foo.txt')
        nexteq('/v/templates/site/en/foo.txt')
        # 5: After all the site-admin override paths have been searched, the
        # Mailman in-tree paths are searched.  Note that Mailman only ships
        # one set of English templates.
        nexteq('/m/templates/en/foo.txt')

    def test_no_language_argument_search_order(self):
        search_order = self._stripped_search_order('foo.txt', self.mlist)
        # For convenience.
        def nexteq(path):                                  # noqa: E306
            self.assertEqual(next(search_order), path)
        # 1: Use mlist.preferred_language
        nexteq('/v/templates/lists/l.example.com/de/foo.txt')
        nexteq('/v/templates/lists/l@example.com/de/foo.txt')
        nexteq('/v/templates/domains/example.com/de/foo.txt')
        nexteq('/v/templates/site/de/foo.txt')
        # 2: Use the site's default language
        nexteq('/v/templates/lists/l.example.com/fr/foo.txt')
        nexteq('/v/templates/lists/l@example.com/fr/foo.txt')
        nexteq('/v/templates/domains/example.com/fr/foo.txt')
        nexteq('/v/templates/site/fr/foo.txt')
        # 3: English
        nexteq('/v/templates/lists/l.example.com/en/foo.txt')
        nexteq('/v/templates/lists/l@example.com/en/foo.txt')
        nexteq('/v/templates/domains/example.com/en/foo.txt')
        nexteq('/v/templates/site/en/foo.txt')
        # 4: After all the site-admin override paths have been searched, the
        # Mailman in-tree paths are searched.  Note that Mailman only ships
        # one set of English templates.
        nexteq('/m/templates/en/foo.txt')

    def test_no_mailing_list_argument_search_order(self):
        search_order = self._stripped_search_order('foo.txt', language='it')
        # For convenience.
        def nexteq(path):                                  # noqa: E306
            self.assertEqual(next(search_order), path)
        # 1: Use the given language argument
        nexteq('/v/templates/site/it/foo.txt')
        # 2: Use the site's default language
        nexteq('/v/templates/site/fr/foo.txt')
        # 3: English
        nexteq('/v/templates/site/en/foo.txt')
        # 4: After all the site-admin override paths have been searched, the
        # Mailman in-tree paths are searched.  Note that Mailman only ships
        # one set of English templates.
        nexteq('/m/templates/en/foo.txt')

    def test_no_optional_arguments_search_order(self):
        search_order = self._stripped_search_order('foo.txt')
        # For convenience.
        def nexteq(path):                                        # noqa: E306
            self.assertEqual(next(search_order), path)
        # 1: Use the site's default language
        nexteq('/v/templates/site/fr/foo.txt')
        # 2: English
        nexteq('/v/templates/site/en/foo.txt')
        # 3: After all the site-admin override paths have been searched, the
        # Mailman in-tree paths are searched.  Note that Mailman only ships
        # one set of English templates.
        nexteq('/m/templates/en/foo.txt')


class TestFind(unittest.TestCase):
    """Test template search."""

    layer = ConfigLayer

    def setUp(self):
        self.var_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.var_dir)
        config.push('template config', """\
        [paths.testing]
        var_dir: {}
        """.format(self.var_dir))
        self.addCleanup(config.pop, 'template config')
        # The following MUST happen AFTER the push() above since pushing a new
        # config also clears out the language manager.
        getUtility(ILanguageManager).add('xx', 'utf-8', 'Xlandia')
        self.mlist = create_list('test@example.com')
        self.mlist.preferred_language = 'xx'
        self.fp = None
        # Populate the template directories with a few fake templates.
        def write(text, path):                             # noqa: E306
            os.makedirs(os.path.dirname(path))
            with open(path, 'w') as fp:
                fp.write(text)
        self.xxsite = os.path.join(
            self.var_dir, 'templates', 'site', 'xx', 'site.txt')
        write('Site template', self.xxsite)
        self.xxdomain = os.path.join(
              self.var_dir, 'templates',
              'domains', 'example.com', 'xx', 'domain.txt')
        write('Domain template', self.xxdomain)
        self.xxlist = os.path.join(
              self.var_dir, 'templates',
              'lists', 'test@example.com', 'xx', 'list.txt')
        write('List template', self.xxlist)

    def tearDown(self):
        if self.fp is not None:
            self.fp.close()

    def test_find_site_template(self):
        filename, self.fp = find('site.txt', language='xx')
        self.assertEqual(filename, self.xxsite)
        self.assertEqual(self.fp.read(), 'Site template')

    def test_find_domain_template(self):
        filename, self.fp = find('domain.txt', self.mlist)
        self.assertEqual(filename, self.xxdomain)
        self.assertEqual(self.fp.read(), 'Domain template')

    def test_find_list_template(self):
        filename, self.fp = find('list.txt', self.mlist)
        self.assertEqual(filename, self.xxlist)
        self.assertEqual(self.fp.read(), 'List template')

    def test_template_not_found(self):
        with self.assertRaises(TemplateNotFoundError) as cm:
            find('missing.txt', self.mlist)
        self.assertEqual(cm.exception.template_file, 'missing.txt')
