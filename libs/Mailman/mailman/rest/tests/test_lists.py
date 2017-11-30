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

"""REST list tests."""

import unittest

from datetime import timedelta
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.database.transaction import transaction
from mailman.interfaces.digests import DigestFrequency
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.mailinglist import IAcceptableAliasSet
from mailman.interfaces.member import DeliveryMode
from mailman.interfaces.template import ITemplateManager
from mailman.interfaces.usermanager import IUserManager
from mailman.model.mailinglist import AcceptableAlias
from mailman.runners.digest import DigestRunner
from mailman.testing.helpers import (
    call_api, get_queue_messages, make_testable_runner,
    specialized_message_from_string as mfs)
from mailman.testing.layers import RESTLayer
from mailman.utilities.datetime import now as right_now
from urllib.error import HTTPError
from zope.component import getUtility


class TestListsMissing(unittest.TestCase):
    """Test expected failures."""

    layer = RESTLayer

    def test_missing_list_roster_member_404(self):
        # /lists/<missing>/roster/member gives 404
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/missing@example.com'
                     '/roster/member')
        self.assertEqual(cm.exception.code, 404)

    def test_missing_list_roster_owner_404(self):
        # /lists/<missing>/roster/owner gives 404
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/missing@example.com'
                     '/roster/owner')
        self.assertEqual(cm.exception.code, 404)

    def test_missing_list_roster_moderator_404(self):
        # /lists/<missing>/roster/member gives 404
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/missing@example.com'
                     '/roster/moderator')
        self.assertEqual(cm.exception.code, 404)

    def test_missing_list_configuration_404(self):
        # /lists/<missing>/config gives 404
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/lists/missing@example.com/config')
        self.assertEqual(cm.exception.code, 404)


class TestLists(unittest.TestCase):
    """Test various aspects of mailing list resources."""

    layer = RESTLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('test@example.com')
        self._usermanager = getUtility(IUserManager)

    def test_member_count_with_no_members(self):
        # The list initially has 0 members.
        json, response = call_api(
            'http://localhost:9001/3.0/lists/test@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['member_count'], 0)

    def test_member_count_with_one_member(self):
        # Add a member to a list and check that the resource reflects this.
        with transaction():
            anne = self._usermanager.create_address('anne@example.com')
            self._mlist.subscribe(anne)
        json, response = call_api(
            'http://localhost:9001/3.0/lists/test@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['member_count'], 1)

    def test_member_count_with_two_members(self):
        # Add two members to a list and check that the resource reflects this.
        with transaction():
            anne = self._usermanager.create_address('anne@example.com')
            self._mlist.subscribe(anne)
            bart = self._usermanager.create_address('bar@example.com')
            self._mlist.subscribe(bart)
        json, response = call_api(
            'http://localhost:9001/3.0/lists/test@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['member_count'], 2)

    def test_query_for_lists_in_missing_domain(self):
        # You cannot ask all the mailing lists in a non-existent domain.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/domains/no.example.org/lists')
        self.assertEqual(cm.exception.code, 404)

    def test_cannot_create_list_in_missing_domain(self):
        # You cannot create a mailing list in a domain that does not exist.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists', {
                     'fqdn_listname': 'ant@no-domain.example.org',
                     })
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason,
                         'Domain does not exist: no-domain.example.org')

    def test_cannot_create_list_with_invalid_posting_address(self):
        # You cannot create a mailing list which would have an invalid list
        # posting address.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists', {
                     'fqdn_listname': '@example.com',
                     })
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason,
                         'Invalid list posting address: @example.com')

    def test_cannot_create_list_with_invalid_name(self):
        # You cannot create a mailing list which would have an invalid list
        # posting address.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists', {
                     'fqdn_listname': 'a/list@example.com',
                     })
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason,
                         'Invalid list name: a/list')

    def test_cannot_create_duplicate_list(self):
        # You cannot create a list that already exists.
        call_api('http://localhost:9001/3.0/lists', {
                 'fqdn_listname': 'ant@example.com',
                 })
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists', {
                     'fqdn_listname': 'ant@example.com',
                     })
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason, 'Mailing list exists')

    def test_cannot_delete_missing_list(self):
        # You cannot delete a list that does not exist.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/bee.example.com',
                     method='DELETE')
        self.assertEqual(cm.exception.code, 404)

    def test_cannot_delete_already_deleted_list(self):
        # You cannot delete a list twice.
        call_api('http://localhost:9001/3.0/lists', {
                 'fqdn_listname': 'ant@example.com',
                 })
        call_api('http://localhost:9001/3.0/lists/ant.example.com',
                 method='DELETE')
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/ant.example.com',
                     method='DELETE')
        self.assertEqual(cm.exception.code, 404)

    def test_roster(self):
        # Lists have rosters which can be accessed by role.
        with transaction():
            anne = self._usermanager.create_address('anne@example.com')
            bart = self._usermanager.create_address('bart@example.com')
            self._mlist.subscribe(anne)
            self._mlist.subscribe(bart)
        json, response = call_api(
            'http://localhost:9001/3.0/lists/test@example.com/roster/member')
        self.assertEqual(json['start'], 0)
        self.assertEqual(json['total_size'], 2)
        member = json['entries'][0]
        self.assertEqual(member['email'], 'anne@example.com')
        self.assertEqual(member['role'], 'member')
        member = json['entries'][1]
        self.assertEqual(member['email'], 'bart@example.com')
        self.assertEqual(member['role'], 'member')

    def test_delete_list_with_acceptable_aliases(self):
        # LP: #1432239 - deleting a mailing list with acceptable aliases
        # causes a SQLAlchemy error.  The aliases must be deleted first.
        with transaction():
            alias_set = IAcceptableAliasSet(self._mlist)
            alias_set.add('bee@example.com')
        call_api('http://localhost:9001/3.0/lists/test.example.com',
                 method='DELETE')
        # Neither the mailing list, nor the aliases are present.
        self.assertIsNone(getUtility(IListManager).get('test@example.com'))
        self.assertEqual(config.db.store.query(AcceptableAlias).count(), 0)

    def test_bad_roster_matcher(self):
        # Try to get a list's roster, but the roster name is bogus.
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/ant.example.com'
                     '/roster/bogus')
        self.assertEqual(cm.exception.code, 404)

    def test_bad_config_matcher(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/ant.example.com'
                     '/config/volume/bogus')
        self.assertEqual(cm.exception.code, 404)

    def test_bad_list_get(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/bogus.example.com')
        self.assertEqual(cm.exception.code, 404)

    def test_not_found_member_role(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/test.example.com'
                     '/owner/nobody@example.com')
        self.assertEqual(cm.exception.code, 404)

    def test_list_mass_unsubscribe_all_succeed(self):
        with transaction():
            aperson = self._usermanager.create_address('aperson@example.com')
            bperson = self._usermanager.create_address('bperson@example.com')
            cperson = self._usermanager.create_address('cperson@example.com')
            self._mlist.subscribe(aperson)
            self._mlist.subscribe(bperson)
            self._mlist.subscribe(cperson)
        json, response = call_api(
            'http://localhost:9001/3.0/lists/test.example.com'
            '/roster/member', {
                'emails': ['aperson@example.com',
                           'bperson@example.com',
                           ]},
            'DELETE')
        self.assertEqual(response.status_code, 200)
        # Remove variable data.
        json.pop('http_etag')
        self.assertEqual(json, {
            'aperson@example.com': True,
            'bperson@example.com': True,
            })

    def test_list_mass_unsubscribe_all_fail(self):
        with transaction():
            aperson = self._usermanager.create_address('aperson@example.com')
            bperson = self._usermanager.create_address('bperson@example.com')
            cperson = self._usermanager.create_address('cperson@example.com')
            self._mlist.subscribe(aperson)
            self._mlist.subscribe(bperson)
            self._mlist.subscribe(cperson)
        json, response = call_api(
            'http://localhost:9001/3.0/lists/test.example.com'
            '/roster/member', {
                'emails': ['yperson@example.com',
                           'zperson@example.com',
                           ]},
            'DELETE')
        self.assertEqual(response.status_code, 200)
        # Remove variable data.
        json.pop('http_etag')
        self.assertEqual(json, {
            'yperson@example.com': False,
            'zperson@example.com': False,
            })

    def test_list_mass_unsubscribe_mixed_success(self):
        with transaction():
            aperson = self._usermanager.create_address('aperson@example.com')
            bperson = self._usermanager.create_address('bperson@example.com')
            cperson = self._usermanager.create_address('cperson@example.com')
            self._mlist.subscribe(aperson)
            self._mlist.subscribe(bperson)
            self._mlist.subscribe(cperson)
        json, response = call_api(
            'http://localhost:9001/3.0/lists/test.example.com'
            '/roster/member', {
                'emails': ['aperson@example.com',
                           'zperson@example.com',
                           ]},
            'DELETE')
        self.assertEqual(response.status_code, 200)
        # Remove variable data.
        json.pop('http_etag')
        self.assertEqual(json, {
            'aperson@example.com': True,
            'zperson@example.com': False,
            })

    def test_list_mass_unsubscribe_with_duplicates(self):
        with transaction():
            aperson = self._usermanager.create_address('aperson@example.com')
            bperson = self._usermanager.create_address('bperson@example.com')
            cperson = self._usermanager.create_address('cperson@example.com')
            self._mlist.subscribe(aperson)
            self._mlist.subscribe(bperson)
            self._mlist.subscribe(cperson)
        json, response = call_api(
            'http://localhost:9001/3.0/lists/test.example.com'
            '/roster/member', {
                'emails': ['aperson@example.com',
                           'aperson@example.com',
                           'bperson@example.com',
                           'zperson@example.com',
                           ]},
            'DELETE')
        self.assertEqual(response.status_code, 200)
        # Remove variable data.
        json.pop('http_etag')
        self.assertEqual(json, {
            'aperson@example.com': True,
            'bperson@example.com': True,
            'zperson@example.com': False,
            })

    def test_list_mass_unsubscribe_bogus_list(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/bogus.example.com'
                     '/roster/member',
                     None, 'DELETE')
        self.assertEqual(cm.exception.code, 404)

    def test_list_mass_unsubscribe_with_no_data(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/test.example.com'
                     '/roster/member',
                     None, 'DELETE')
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason, 'Missing parameters: emails')


class TestListArchivers(unittest.TestCase):
    """Test corner cases for list archivers."""

    layer = RESTLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('ant@example.com')

    def test_archiver_statuses(self):
        json, response = call_api(
            'http://localhost:9001/3.0/lists/ant.example.com/archivers')
        self.assertEqual(response.status_code, 200)
        # Remove the variable data.
        json.pop('http_etag')
        self.assertEqual(json, {
            'mail-archive': True,
            'mhonarc': True,
            })

    def test_archiver_statuses_on_missing_lists(self):
        # You cannot get the archiver statuses on a list that doesn't exist.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/lists/bee.example.com/archivers')
        self.assertEqual(cm.exception.code, 404)

    def test_put_bogus_archiver(self):
        # You cannot PUT on an archiver the list doesn't know about.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/lists/ant.example.com/archivers', {
                    'bogus-archiver': True,
                    },
                method='PUT')
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason,
                         'Unexpected parameters: bogus-archiver')

    def test_patch_bogus_archiver(self):
        # You cannot PATCH on an archiver the list doesn't know about.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/lists/ant.example.com/archivers', {
                    'bogus-archiver': True,
                    },
                method='PATCH')
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason,
                         'Unexpected parameters: bogus-archiver')

    def test_put_incomplete_statuses(self):
        # PUT requires the full resource representation.  This one forgets to
        # specify the mhonarc archiver.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/lists/ant.example.com/archivers', {
                    'mail-archive': True,
                    },
                method='PUT')
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason, 'Missing parameters: mhonarc')

    def test_patch_bogus_status(self):
        # Archiver statuses must be interpretable as booleans.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/lists/ant.example.com/archivers', {
                    'mail-archive': 'sure',
                    'mhonarc': 'no'
                    },
                method='PATCH')
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason, 'Invalid boolean value: sure')


class TestListPagination(unittest.TestCase):
    """Test mailing list pagination functionality.

    We create a bunch of mailing lists within a domain.  When we want to
    get all the lists in that domain via the REST API, we need to
    paginate over them, otherwise there could be too many for display.
    """

    layer = RESTLayer

    def setUp(self):
        with transaction():
            # Create a bunch of mailing lists in the example.com domain.
            create_list('ant@example.com')
            create_list('bee@example.com')
            create_list('cat@example.com')
            create_list('dog@example.com')
            create_list('emu@example.com')
            create_list('fly@example.com')

    def test_first_page(self):
        json, response = call_api(
            'http://localhost:9001/3.0/domains/example.com/lists'
            '?count=1&page=1')
        # There are 6 total lists, but only the first one in the page.
        self.assertEqual(json['total_size'], 6)
        self.assertEqual(json['start'], 0)
        self.assertEqual(len(json['entries']), 1)
        entry = json['entries'][0]
        self.assertEqual(entry['fqdn_listname'], 'ant@example.com')

    def test_second_page(self):
        json, response = call_api(
            'http://localhost:9001/3.0/domains/example.com/lists'
            '?count=1&page=2')
        # There are 6 total lists, but only the first one in the page.
        self.assertEqual(json['total_size'], 6)
        self.assertEqual(json['start'], 1)
        self.assertEqual(len(json['entries']), 1)
        entry = json['entries'][0]
        self.assertEqual(entry['fqdn_listname'], 'bee@example.com')

    def test_last_page(self):
        json, response = call_api(
            'http://localhost:9001/3.0/domains/example.com/lists'
            '?count=1&page=6')
        # There are 6 total lists, but only the first one in the page.
        self.assertEqual(json['total_size'], 6)
        self.assertEqual(json['start'], 5)
        self.assertEqual(len(json['entries']), 1)
        entry = json['entries'][0]
        self.assertEqual(entry['fqdn_listname'], 'fly@example.com')

    def test_zeroth_page(self):
        # Page numbers start at one.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/domains/example.com/lists'
                '?count=1&page=0')
        self.assertEqual(cm.exception.code, 400)

    def test_negative_page(self):
        # Negative pages are not allowed.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/domains/example.com/lists'
                '?count=1&page=-1')
        self.assertEqual(cm.exception.code, 400)

    def test_past_last_page(self):
        # The 7th page doesn't exist so the collection is empty.
        json, response = call_api(
            'http://localhost:9001/3.0/domains/example.com/lists'
            '?count=1&page=7')
        # There are 6 total lists, but only the first one in the page.
        self.assertEqual(json['total_size'], 6)
        self.assertEqual(json['start'], 6)
        self.assertNotIn('entries', json)


class TestListDigests(unittest.TestCase):
    """Test /lists/<list-id>/digest"""

    layer = RESTLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('ant@example.com')
            self._mlist.send_welcome_message = False
            anne = getUtility(IUserManager).create_address('anne@example.com')
            self._mlist.subscribe(anne)
            anne.preferences.delivery_mode = DeliveryMode.plaintext_digests

    def test_bad_digest_url(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/lists/bogus.example.com/digest')
        self.assertEqual(cm.exception.code, 404)

    def test_post_nothing_to_do(self):
        json, response = call_api(
            'http://localhost:9001/3.0/lists/ant.example.com/digest', {})
        self.assertEqual(response.status_code, 200)

    def test_post_something_to_do(self):
        json, response = call_api(
            'http://localhost:9001/3.0/lists/ant.example.com/digest', dict(
                bump=True))
        self.assertEqual(response.status_code, 202)

    def test_post_bad_request(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/lists/ant.example.com/digest', dict(
                    bogus=True))
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.reason, 'Unexpected parameters: bogus')

    def test_bump_before_send(self):
        with transaction():
            self._mlist.digest_volume_frequency = DigestFrequency.monthly
            self._mlist.volume = 7
            self._mlist.next_digest_number = 4
            self._mlist.digest_last_sent_at = right_now() + timedelta(
                days=-32)
        msg = mfs("""\
To: ant@example.com
From: anne@example.com
Subject: message 1

""")
        config.handlers['to-digest'].process(self._mlist, msg, {})
        json, response = call_api(
            'http://localhost:9001/3.0/lists/ant.example.com/digest', dict(
                send=True,
                bump=True))
        self.assertEqual(response.status_code, 202)
        make_testable_runner(DigestRunner, 'digest').run()
        # The volume is 8 and the digest number is 2 because a digest was sent
        # after the volume/number was bumped.
        self.assertEqual(self._mlist.volume, 8)
        self.assertEqual(self._mlist.next_digest_number, 2)
        self.assertEqual(self._mlist.digest_last_sent_at, right_now())
        items = get_queue_messages('virgin')
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].msg['subject'], 'Ant Digest, Vol 8, Issue 1')


class TestListTemplates(unittest.TestCase):
    """Test /lists/<list-id>/uris"""

    layer = RESTLayer

    def setUp(self):
        with transaction():
            self._mlist = create_list('ant@example.com')

    def test_no_templates_for_api_30(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.0/lists/ant.example.com/uris')
        self.assertEqual(cm.exception.code, 404)

    def test_no_templates_for_missing_list(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.1/lists/bee.example.com/uris')
        self.assertEqual(cm.exception.code, 404)

    def test_path_too_long(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.1/lists/ant.example.com/uris'
                     '/foo/bar')
        self.assertEqual(cm.exception.code, 400)

    def test_get_unknown_uri(self):
        with self.assertRaises(HTTPError) as cm:
            call_api('http://localhost:9001/3.1/lists/ant.example.com/uris'
                     '/not:a:template')
        self.assertEqual(cm.exception.code, 404)

    def test_get_all_uris(self):
        manager = getUtility(ITemplateManager)
        with transaction():
            manager.set(
                'list:user:notice:welcome', 'ant.example.com',
                'http://example.com/welcome')
            manager.set(
                'list:user:notice:goodbye', 'ant.example.com',
                'http://example.com/goodbye',
                'a user', 'the password',
                )
        json, response = call_api(
            'http://localhost:9001/3.1/lists/ant.example.com/uris')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json['start'], 0)
        self.assertEqual(json['total_size'], 2)
        self.assertEqual(
            json['self_link'],
            'http://localhost:9001/3.1/lists/ant.example.com/uris')
        self.assertEqual(json['entries'], [
            {'http_etag': '"6612187ed6604ce54a57405fd66742557391ed4a"',
             'name': 'list:user:notice:goodbye',
             'password': 'the password',
             'self_link': ('http://localhost:9001/3.1/lists/ant.example.com'
                           '/uris/list:user:notice:goodbye'),
             'uri': 'http://example.com/goodbye',
             'username': 'a user',
             },
            {'http_etag': '"cb1ab5eee2242143d2984edd0487532915ad3a8e"',
             'name': 'list:user:notice:welcome',
             'self_link': ('http://localhost:9001/3.1/lists/ant.example.com'
                           '/uris/list:user:notice:welcome'),
             'uri': 'http://example.com/welcome',
             }])

    def test_patch_uris(self):
        json, response = call_api(
            'http://localhost:9001/3.1/lists/ant.example.com/uris', {
                'list:user:notice:welcome': 'http://example.org/welcome',
                'list:user:notice:goodbye': 'http://example.org/goodbye',
                }, method='PATCH')
        self.assertEqual(response.status_code, 204)
        manager = getUtility(ITemplateManager)
        template = manager.raw('list:user:notice:welcome', 'ant.example.com')
        self.assertEqual(template.uri, 'http://example.org/welcome')
        self.assertIsNone(template.username)
        self.assertEqual(template.password, '')
        template = manager.raw('list:user:notice:goodbye', 'ant.example.com')
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertIsNone(template.username)
        self.assertEqual(template.password, '')

    def test_patch_uris_with_credentials(self):
        json, response = call_api(
            'http://localhost:9001/3.1/lists/ant.example.com/uris', {
                'list:user:notice:welcome': 'http://example.org/welcome',
                'list:user:notice:goodbye': 'http://example.org/goodbye',
                'password': 'some password',
                'username': 'anne.person',
                }, method='PATCH')
        self.assertEqual(response.status_code, 204)
        manager = getUtility(ITemplateManager)
        template = manager.raw('list:user:notice:welcome', 'ant.example.com')
        self.assertEqual(template.uri, 'http://example.org/welcome')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:user:notice:goodbye', 'ant.example.com')
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')

    def test_patch_uris_with_partial_credentials(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/lists/ant.example.com/uris', {
                    'list:user:notice:welcome': 'http://example.org/welcome',
                    'list:user:notice:goodbye': 'http://example.org/goodbye',
                    'username': 'anne.person',
                    }, method='PATCH')
        self.assertEqual(cm.exception.code, 400)

    def test_put_all_uris(self):
        json, response = call_api(
            'http://localhost:9001/3.1/lists/ant.example.com/uris', {
                'list:admin:action:post': '',
                'list:admin:action:subscribe': '',
                'list:admin:action:unsubscribe': '',
                'list:admin:notice:subscribe': '',
                'list:admin:notice:unrecognized': '',
                'list:admin:notice:unsubscribe': '',
                'list:member:digest:footer': '',
                'list:member:digest:header': '',
                'list:member:digest:masthead': '',
                'list:member:regular:footer': 'http://example.org/footer',
                'list:member:regular:header': 'http://example.org/header',
                'list:user:action:subscribe': '',
                'list:user:action:unsubscribe': '',
                'list:user:notice:goodbye': 'http://example.org/goodbye',
                'list:user:notice:hold': '',
                'list:user:notice:no-more-today': '',
                'list:user:notice:post': '',
                'list:user:notice:probe': '',
                'list:user:notice:refuse': '',
                'list:user:notice:welcome': 'http://example.org/welcome',
                'password': 'some password',
                'username': 'anne.person',
                }, method='PUT')
        self.assertEqual(response.status_code, 204)
        manager = getUtility(ITemplateManager)
        template = manager.raw('list:member:digest:footer', 'ant.example.com')
        self.assertIsNone(template)
        template = manager.raw('list:member:digest:header', 'ant.example.com')
        self.assertIsNone(template)
        template = manager.raw('list:member:regular:footer', 'ant.example.com')
        self.assertEqual(template.uri, 'http://example.org/footer')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:member:regular:header', 'ant.example.com')
        self.assertEqual(template.uri, 'http://example.org/header')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:user:notice:goodbye', 'ant.example.com')
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')
        template = manager.raw('list:user:notice:goodbye', 'ant.example.com')
        self.assertEqual(template.uri, 'http://example.org/goodbye')
        self.assertEqual(template.username, 'anne.person')
        self.assertEqual(template.password, 'some password')

    def test_delete_all_uris(self):
        manager = getUtility(ITemplateManager)
        with transaction():
            manager.set(
                'list:user:notice:welcome', 'ant.example.com',
                'http://example.com/welcome')
            manager.set(
                'list:user:notice:goodbye', 'ant.example.com',
                'http://example.com/goodbye',
                'a user', 'the password',
                )
        json, response = call_api(
            'http://localhost:9001/3.1/lists/ant.example.com/uris',
            method='DELETE')
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(
            manager.raw('list:user:notice:welcome', 'ant.example.com'))
        self.assertIsNone(
            manager.raw('list:user:notice:goodbye', 'ant.example.com'))

    def test_get_a_url(self):
        with transaction():
            getUtility(ITemplateManager).set(
                'list:user:notice:welcome', 'ant.example.com',
                'http://example.com/welcome')
        json, response = call_api(
            'http://localhost:9001/3.1/lists/ant.example.com/uris'
            '/list:user:notice:welcome')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json, {
            'http_etag': '"36f8bef800cfd278f097c61c5892a34c0650f4aa"',
            'self_link': ('http://localhost:9001/3.1/lists/ant.example.com'
                          '/uris/list:user:notice:welcome'),
            'uri': 'http://example.com/welcome',
            })

    def test_get_a_bad_url(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/lists/ant.example.com/uris'
                '/list:user:notice:notemplate')
        self.assertEqual(cm.exception.code, 404)

    def test_get_unset_url(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/lists/ant.example.com/uris'
                '/list:user:notice:welcome')
        self.assertEqual(cm.exception.code, 404)

    def test_patch_url_with_too_many_parameters(self):
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.1/lists/ant.example.com/uris', {
                    'list:user:notice:welcome': 'http://example.org/welcome',
                    'list:user:notice:goodbye': 'http://example.org/goodbye',
                    'secret': 'some password',
                    'person': 'anne.person',
                    }, method='PATCH')
        self.assertEqual(cm.exception.code, 400)

    def test_deprecated_resources(self):
        # This resource does not exist with API 3.0.
        with self.assertRaises(HTTPError) as cm:
            call_api(
                'http://localhost:9001/3.0/templates/ant@example.com'
                '/footer/en')
        self.assertEqual(cm.exception.code, 404)
