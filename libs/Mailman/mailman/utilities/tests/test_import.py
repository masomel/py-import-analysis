# Copyright (C) 2010-2017 by the Free Software Foundation, Inc.
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

"""Tests for config.pck imports."""

import os
import unittest

from datetime import timedelta, datetime
from enum import Enum
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.handlers.decorate import decorate
from mailman.interfaces.action import Action, FilterAction
from mailman.interfaces.address import InvalidEmailAddressError
from mailman.interfaces.archiver import ArchivePolicy
from mailman.interfaces.autorespond import ResponseAction
from mailman.interfaces.bans import IBanManager
from mailman.interfaces.bounce import UnrecognizedBounceDisposition
from mailman.interfaces.domain import IDomainManager
from mailman.interfaces.languages import ILanguageManager
from mailman.interfaces.mailinglist import (
    IAcceptableAliasSet, SubscriptionPolicy)
from mailman.interfaces.member import DeliveryMode, DeliveryStatus
from mailman.interfaces.nntp import NewsgroupModeration
from mailman.interfaces.template import ITemplateLoader, ITemplateManager
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import LogFileMark
from mailman.testing.layers import ConfigLayer
from mailman.utilities.filesystem import makedirs
from mailman.utilities.importer import (
    Import21Error, check_language_code, import_config_pck)
from pickle import load
from pkg_resources import resource_filename
from unittest import mock
from urllib.error import URLError
from zope.component import getUtility


NL = '\n'


class DummyEnum(Enum):
    # For testing purposes
    val = 42


def list_to_string(data):
    return NL.join(data).encode('utf-8')


class TestBasicImport(unittest.TestCase):
    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        self._mlist = create_list('blank@example.com')
        pickle_file = resource_filename('mailman.testing', 'config.pck')
        with open(pickle_file, 'rb') as fp:
            self._pckdict = load(fp)

    def _import(self):
        import_config_pck(self._mlist, self._pckdict)

    def test_display_name(self):
        # The mlist.display_name gets set from the old list's real_name.
        self.assertEqual(self._mlist.display_name, 'Blank')
        self._import()
        self.assertEqual(self._mlist.display_name, 'Test')

    def test_mail_host_invariant(self):
        # The mlist.mail_host must not be updated when importing (it will
        # change the list_id property, which is supposed to be read-only).
        self.assertEqual(self._mlist.mail_host, 'example.com')
        self._import()
        self.assertEqual(self._mlist.mail_host, 'example.com')

    def test_rfc2369_headers(self):
        self._mlist.allow_list_posts = False
        self._mlist.include_rfc2369_headers = False
        self._import()
        self.assertTrue(self._mlist.allow_list_posts)
        self.assertTrue(self._mlist.include_rfc2369_headers)

    def test_no_overwrite_rosters(self):
        # The mlist.members and mlist.digest_members rosters must not be
        # overwritten.
        for rname in ('members', 'digest_members'):
            roster = getattr(self._mlist, rname)
            self.assertFalse(isinstance(roster, dict))
            # Suppress warning messages in test output.
            with mock.patch('sys.stderr'):
                self._import()
            self.assertFalse(
                isinstance(roster, dict),
                'The %s roster has been overwritten by the import' % rname)

    def test_last_post_time(self):
        # last_post_time -> last_post_at
        self._pckdict['last_post_time'] = 1270420800.274485
        self.assertEqual(self._mlist.last_post_at, None)
        self._import()
        # convert 1270420800.2744851 to datetime
        expected = datetime(2010, 4, 4, 22, 40, 0, 274485)
        self.assertEqual(self._mlist.last_post_at, expected)

    def test_autoresponse_grace_period(self):
        # autoresponse_graceperiod -> autoresponse_grace_period
        # must be a timedelta, not an int
        self._mlist.autoresponse_grace_period = timedelta(days=42)
        self._import()
        self.assertTrue(
            isinstance(self._mlist.autoresponse_grace_period, timedelta))
        self.assertEqual(self._mlist.autoresponse_grace_period,
                         timedelta(days=90))

    def test_autoresponse_admin_to_owner(self):
        # admin -> owner
        self._mlist.autorespond_owner = DummyEnum.val
        self._mlist.autoresponse_owner_text = 'DUMMY'
        self._import()
        self.assertEqual(self._mlist.autorespond_owner, ResponseAction.none)
        self.assertEqual(self._mlist.autoresponse_owner_text, '')

    def test_administrativia(self):
        self._mlist.administrivia = None
        self._import()
        self.assertTrue(self._mlist.administrivia)

    def test_filter_pass_renames(self):
        # mime_types -> types
        # filename_extensions -> extensions
        self._mlist.filter_types = ['dummy']
        self._mlist.pass_types = ['dummy']
        self._mlist.filter_extensions = ['dummy']
        self._mlist.pass_extensions = ['dummy']
        self._import()
        self.assertEqual(list(self._mlist.filter_types), [])
        self.assertEqual(list(self._mlist.filter_extensions),
                         ['exe', 'bat', 'cmd', 'com', 'pif',
                          'scr', 'vbs', 'cpl'])
        self.assertEqual(
            list(self._mlist.pass_types),
            ['multipart/mixed', 'multipart/alternative', 'text/plain'])
        self.assertEqual(list(self._mlist.pass_extensions), [])

    def test_process_bounces(self):
        # bounce_processing -> process_bounces
        self._mlist.process_bounces = None
        self._import()
        self.assertTrue(self._mlist.process_bounces)

    def test_forward_unrecognized_bounces_to(self):
        # bounce_unrecognized_goes_to_list_owner
        #   -> forward_unrecognized_bounces_to
        self._mlist.forward_unrecognized_bounces_to = DummyEnum.val
        self._import()
        self.assertEqual(self._mlist.forward_unrecognized_bounces_to,
                         UnrecognizedBounceDisposition.administrators)

    def test_moderator_password(self):
        # mod_password -> moderator_password
        self._mlist.moderator_password = b'TESTDATA'
        self._import()
        self.assertEqual(self._mlist.moderator_password, None)

    def test_moderator_password_str(self):
        # moderator_password must not be unicode
        self._pckdict['mod_password'] = b'TESTVALUE'
        self._import()
        self.assertNotIsInstance(self._mlist.moderator_password, str)
        self.assertEqual(self._mlist.moderator_password, b'TESTVALUE')

    def test_newsgroup_moderation(self):
        # news_moderation -> newsgroup_moderation
        # news_prefix_subject_too -> nntp_prefix_subject_too
        self._mlist.newsgroup_moderation = DummyEnum.val
        self._mlist.nntp_prefix_subject_too = None
        self._import()
        self.assertEqual(self._mlist.newsgroup_moderation,
                         NewsgroupModeration.none)
        self.assertTrue(self._mlist.nntp_prefix_subject_too)

    def test_msg_to_message(self):
        # send_welcome_msg -> send_welcome_message
        # send_goodbye_msg -> send_goodbye_message
        self._mlist.send_welcome_message = None
        self._mlist.send_goodbye_message = None
        self._import()
        self.assertTrue(self._mlist.send_welcome_message)
        self.assertTrue(self._mlist.send_goodbye_message)

    def test_ban_list(self):
        banned = [
            ('anne@example.com', 'anne@example.com'),
            ('^.*@example.com', 'bob@example.com'),
            ('non-ascii-\xe8@example.com', 'non-ascii-\ufffd@example.com'),
            ]
        self._pckdict['ban_list'] = [b[0].encode('iso-8859-1') for b in banned]
        self._import()
        for _pattern, addr in banned:
            self.assertTrue(IBanManager(self._mlist).is_banned(addr))

    def test_acceptable_aliases(self):
        # This used to be a plain-text field (values are newline-separated).
        aliases = ['alias1@example.com',
                   'alias2@exemple.com',
                   'non-ascii-\xe8@example.com',
                   ]
        self._pckdict['acceptable_aliases'] = list_to_string(aliases)
        self._import()
        alias_set = IAcceptableAliasSet(self._mlist)
        self.assertEqual(sorted(alias_set.aliases), aliases)

    def test_acceptable_aliases_invalid(self):
        # Values without an '@' sign used to be matched against the local
        # part, now we need to add the '^' sign to indicate it's a regexp.
        aliases = ['invalid-value']
        self._pckdict['acceptable_aliases'] = list_to_string(aliases)
        self._import()
        alias_set = IAcceptableAliasSet(self._mlist)
        self.assertEqual(sorted(alias_set.aliases),
                         [('^' + alias) for alias in aliases])

    def test_acceptable_aliases_as_list(self):
        # In some versions of the pickle, this can be a list, not a string
        # (seen in the wild).
        aliases = [b'alias1@example.com', b'alias2@exemple.com']
        self._pckdict['acceptable_aliases'] = aliases
        self._import()
        alias_set = IAcceptableAliasSet(self._mlist)
        self.assertEqual(sorted(alias_set.aliases),
                         sorted(a.decode('utf-8') for a in aliases))

    def test_info_non_ascii(self):
        # info can contain non-ascii characters.
        info = 'O idioma aceito \xe9 somente Portugu\xeas do Brasil'
        self._pckdict['info'] = info.encode('utf-8')
        self._import()
        self.assertEqual(self._mlist.info, info,
                         'Encoding to UTF-8 is not handled')
        # Test fallback to ascii with replace.
        self._pckdict['info'] = info.encode('iso-8859-1')
        # Suppress warning messages in test output.
        with mock.patch('sys.stderr'):
            self._import()
        self.assertEqual(
            self._mlist.info,
            self._pckdict['info'].decode('ascii', 'replace'),
            "We don't fall back to replacing non-ascii chars")

    def test_preferred_language(self):
        self._pckdict['preferred_language'] = b'ja'
        english = getUtility(ILanguageManager).get('en')
        japanese = getUtility(ILanguageManager).get('ja')
        self.assertEqual(self._mlist.preferred_language, english)
        self._import()
        self.assertEqual(self._mlist.preferred_language, japanese)

    def test_preferred_language_unknown_previous(self):
        # When the previous language is unknown, it should not fail.
        self._mlist._preferred_language = 'xx'
        self._import()
        english = getUtility(ILanguageManager).get('en')
        self.assertEqual(self._mlist.preferred_language, english)

    def test_new_language(self):
        self._pckdict['preferred_language'] = b'xx_XX'
        try:
            self._import()
        except Import21Error as error:
            # Check the message.
            self.assertIn('[language.xx_XX]', str(error))
        else:
            self.fail('Import21Error was not raised')

    def test_encode_ascii_prefixes(self):
        self._pckdict['encode_ascii_prefixes'] = 2
        self.assertEqual(self._mlist.encode_ascii_prefixes, False)
        self._import()
        self.assertEqual(self._mlist.encode_ascii_prefixes, True)

    def test_subscription_policy_open(self):
        self._mlist.subscription_policy = SubscriptionPolicy.confirm
        self._pckdict['subscribe_policy'] = 0
        self._import()
        self.assertEqual(self._mlist.subscription_policy,
                         SubscriptionPolicy.open)

    def test_subscription_policy_confirm(self):
        self._mlist.subscription_policy = SubscriptionPolicy.open
        self._pckdict['subscribe_policy'] = 1
        self._import()
        self.assertEqual(self._mlist.subscription_policy,
                         SubscriptionPolicy.confirm)

    def test_subscription_policy_moderate(self):
        self._mlist.subscription_policy = SubscriptionPolicy.open
        self._pckdict['subscribe_policy'] = 2
        self._import()
        self.assertEqual(self._mlist.subscription_policy,
                         SubscriptionPolicy.moderate)

    def test_subscription_policy_confirm_then_moderate(self):
        self._mlist.subscription_policy = SubscriptionPolicy.open
        self._pckdict['subscribe_policy'] = 3
        self._import()
        self.assertEqual(self._mlist.subscription_policy,
                         SubscriptionPolicy.confirm_then_moderate)

    def test_header_matches(self):
        # This test containes real cases of header_filter_rules.
        self._pckdict['header_filter_rules'] = [
            ('X\\-Spam\\-Status\\: Yes.*', 3, False),
            ('^X-Spam-Status: Yes\r\n\r\n', 2, False),
            ('^X-Spam-Level: \\*\\*\\*.*$', 3, False),
            ('^X-Spam-Level:.\\*\\*\r\n^X-Spam:.Yes', 3, False),
            ('Subject: \\[SPAM\\].*', 3, False),
            ('^Subject: .*loan.*', 3, False),
            ('Original-Received: from *linkedin.com*\r\n', 3, False),
            ('X-Git-Module: rhq.*git', 6, False),
            ('Approved: verysecretpassword', 6, False),
            ('^Subject: dev-\r\n^Subject: staging-', 3, False),
            ('from: .*info@aolanchem.com\r\nfrom: .*@jw-express.com',
             2, False),
            ('^Subject:.*\\Wwas:\\W', 3, False),
            ('^Received: from smtp-.*\\.fedoraproject\\.org\r\n'
             '^Received: from mx.*\\.redhat.com\r\n'
             '^Resent-date:\r\n'
             '^Resent-from:\r\n'
             '^Resent-Message-ID:\r\n'
             '^Resent-to:\r\n'
             '^Subject: [^mtv]\r\n',
             7, False),
            ('^Received: from fedorahosted\\.org.*by fedorahosted\\.org\r\n'
             '^Received: from hosted.*\\.fedoraproject.org.*by '
             'hosted.*\\.fedoraproject\\.org\r\n'
             '^Received: from hosted.*\\.fedoraproject.org.*by '
                'fedoraproject\\.org\r\n'
             '^Received: from hosted.*\\.fedoraproject.org.*by '
                'fedorahosted\\.org',
             6, False),
            ]
        error_log = LogFileMark('mailman.error')
        self._import()
        self.assertListEqual(
            [(hm.header, hm.pattern, hm.chain)
             for hm in self._mlist.header_matches], [
                ('x-spam-status', 'Yes.*', 'discard'),
                ('x-spam-status', 'Yes', 'reject'),
                ('x-spam-level', '\\*\\*\\*.*$', 'discard'),
                ('x-spam-level', '\\*\\*', 'discard'),
                ('x-spam', 'Yes', 'discard'),
                ('subject', '\\[SPAM\\].*', 'discard'),
                ('subject', '.*loan.*', 'discard'),
                ('original-received', 'from *linkedin.com*', 'discard'),
                ('x-git-module', 'rhq.*git', 'accept'),
                ('approved', 'verysecretpassword', 'accept'),
                ('subject', 'dev-', 'discard'),
                ('subject', 'staging-', 'discard'),
                ('from', '.*info@aolanchem.com', 'reject'),
                ('from', '.*@jw-express.com', 'reject'),
                ('subject', '\\Wwas:\\W', 'discard'),
                ('received', 'from smtp-.*\\.fedoraproject\\.org', 'hold'),
                ('received', 'from mx.*\\.redhat.com', 'hold'),
                ('resent-date', '.*', 'hold'),
                ('resent-from', '.*', 'hold'),
                ('resent-message-id', '.*', 'hold'),
                ('resent-to', '.*', 'hold'),
                ('subject', '[^mtv]', 'hold'),
                ('received', 'from fedorahosted\\.org.*by fedorahosted\\.org',
                 'accept'),
                ('received',
                 'from hosted.*\\.fedoraproject.org.*by '
                    'hosted.*\\.fedoraproject\\.org', 'accept'),
                ('received',
                 'from hosted.*\\.fedoraproject.org.*by '
                    'fedoraproject\\.org', 'accept'),
                ('received',
                 'from hosted.*\\.fedoraproject.org.*by '
                    'fedorahosted\\.org', 'accept'),
                ])
        loglines = error_log.read().strip()
        self.assertEqual(len(loglines), 0)

    def test_header_matches_header_only(self):
        # Check that an empty pattern is skipped.
        self._pckdict['header_filter_rules'] = [
            ('SomeHeaderName', 3, False),
            ]
        error_log = LogFileMark('mailman.error')
        self._import()
        self.assertListEqual(self._mlist.header_matches, [])
        self.assertIn('Unsupported header_filter_rules pattern',
                      error_log.readline())

    def test_header_matches_anything(self):
        # Check that a wild card header pattern is skipped.
        self._pckdict['header_filter_rules'] = [
            ('.*', 7, False),
            ]
        error_log = LogFileMark('mailman.error')
        self._import()
        self.assertListEqual(self._mlist.header_matches, [])
        self.assertIn('Unsupported header_filter_rules pattern',
                      error_log.readline())

    def test_header_matches_invalid_re(self):
        # Check that an invalid regular expression pattern is skipped.
        self._pckdict['header_filter_rules'] = [
            ('SomeHeaderName: *invalid-re', 3, False),
            ]
        error_log = LogFileMark('mailman.error')
        self._import()
        self.assertListEqual(self._mlist.header_matches, [])
        self.assertIn('Skipping header_filter rule because of an invalid '
                      'regular expression', error_log.readline())

    def test_header_matches_defer(self):
        # Check that a defer action is properly converted.
        self._pckdict['header_filter_rules'] = [
            ('^X-Spam-Status: Yes', 0, False),
            ]
        self._import()
        self.assertListEqual(
            [(hm.header, hm.pattern, hm.chain)
             for hm in self._mlist.header_matches],
            [('x-spam-status', 'Yes', None)]
            )

    def test_header_matches_unsupported_action(self):
        # Check that unsupported actions are skipped.
        for action_num in (1, 4, 5):
            self._pckdict['header_filter_rules'] = [
                ('HeaderName: test-re', action_num, False),
                ]
            error_log = LogFileMark('mailman.error')
            self._import()
            self.assertListEqual(self._mlist.header_matches, [])
            self.assertIn('Unsupported header_filter_rules action',
                          error_log.readline())
            # Avoid a useless warning.
            for member in self._mlist.members.members:
                member.unsubscribe()
            for member in self._mlist.owners.members:
                member.unsubscribe()

    def test_header_matches_duplicate(self):
        # Check that duplicate patterns don't cause tracebacks.
        self._pckdict['header_filter_rules'] = [
            ('SomeHeaderName: test-pattern', 3, False),
            ('SomeHeaderName: test-pattern', 2, False),
            ]
        error_log = LogFileMark('mailman.error')
        self._import()
        self.assertListEqual(
            [(hm.header, hm.pattern, hm.chain)
             for hm in self._mlist.header_matches],
            [('someheadername', 'test-pattern', 'discard')]
            )
        self.assertIn('Skipping duplicate header_filter rule',
                      error_log.readline())


class TestArchiveImport(unittest.TestCase):
    """Test conversion of the archive policies.

    Mailman 2.1 had two variables `archive` and `archive_private`.  Now
    there's just a single `archive_policy` enum.
    """
    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('blank@example.com')
        self._mlist.archive_policy = DummyEnum.val

    def _do_test(self, pckdict, expected):
        import_config_pck(self._mlist, pckdict)
        self.assertEqual(self._mlist.archive_policy, expected)

    def test_public(self):
        self._do_test(dict(archive=True, archive_private=False),
                      ArchivePolicy.public)

    def test_private(self):
        self._do_test(dict(archive=True, archive_private=True),
                      ArchivePolicy.private)

    def test_no_archive(self):
        self._do_test(dict(archive=False, archive_private=False),
                      ArchivePolicy.never)

    def test_bad_state(self):
        # For some reason, the old list has the invalid archiving state where
        # `archive` is False and `archive_private` is True.  It doesn't matter
        # because this still collapses to the same enum value.
        self._do_test(dict(archive=False, archive_private=True),
                      ArchivePolicy.never)

    def test_missing_archive_key(self):
        # For some reason, the old list didn't have an `archive` key.  We
        # treat this as if no archiving is done.
        self._do_test(dict(archive_private=False), ArchivePolicy.never)

    def test_missing_archive_key_archive_public(self):
        # For some reason, the old list didn't have an `archive` key, and it
        # has weird value for archive_private.  We treat this as if no
        # archiving is done.
        self._do_test(dict(archive_private=True), ArchivePolicy.never)

    def test_missing_archive_private_key(self):
        # For some reason, the old list was missing an `archive_private` key.
        # For maximum safety, we treat this as private archiving.
        self._do_test(dict(archive=True), ArchivePolicy.private)


class TestFilterActionImport(unittest.TestCase):
    # The mlist.filter_action enum values have changed.  In Mailman 2.1 the
    # order was 'Discard', 'Reject', 'Forward to List Owner', 'Preserve'.

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('blank@example.com')
        self._mlist.filter_action = DummyEnum.val

    def _do_test(self, original, expected):
        import_config_pck(self._mlist, dict(filter_action=original))
        self.assertEqual(self._mlist.filter_action, expected)

    def test_discard(self):
        self._do_test(0, FilterAction.discard)

    def test_reject(self):
        self._do_test(1, FilterAction.reject)

    def test_forward(self):
        self._do_test(2, FilterAction.forward)

    def test_preserve(self):
        self._do_test(3, FilterAction.preserve)


class TestMemberActionImport(unittest.TestCase):
    # The mlist.default_member_action and mlist.default_nonmember_action enum
    # values are different in Mailman 2.1; they have been merged into a
    # single enum in Mailman 3.
    #
    # For default_member_action, which used to be called
    # member_moderation_action, the values were:
    # 0==Hold, 1=Reject, 2==Discard
    #
    # For default_nonmember_action, which used to be called
    # generic_nonmember_action, the values were:
    # 0==Accept, 1==Hold, 2==Reject, 3==Discard

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('blank@example.com')
        self._mlist.default_member_action = DummyEnum.val
        self._mlist.default_nonmember_action = DummyEnum.val
        self._pckdict = dict(
            member_moderation_action=DummyEnum.val,
            generic_nonmember_action=DummyEnum.val,
            )

    def _do_test(self, expected):
        # Suppress warning messages in the test output.
        with mock.patch('sys.stderr'):
            import_config_pck(self._mlist, self._pckdict)
        for key, value in expected.items():
            self.assertEqual(getattr(self._mlist, key), value)

    def test_member_defer(self):
        # If default_member_moderation is not set, the member_moderation_action
        # value is meaningless.
        self._pckdict['default_member_moderation'] = 0
        for mmaval in range(3):
            self._pckdict['member_moderation_action'] = mmaval
            self._do_test(dict(default_member_action=Action.defer))

    def test_member_hold(self):
        self._pckdict['default_member_moderation'] = 1
        self._pckdict['member_moderation_action'] = 0
        self._do_test(dict(default_member_action=Action.hold))

    def test_member_reject(self):
        self._pckdict['default_member_moderation'] = 1
        self._pckdict['member_moderation_action'] = 1
        self._do_test(dict(default_member_action=Action.reject))

    def test_member_discard(self):
        self._pckdict['default_member_moderation'] = 1
        self._pckdict['member_moderation_action'] = 2
        self._do_test(dict(default_member_action=Action.discard))

    def test_nonmember_accept(self):
        self._pckdict['generic_nonmember_action'] = 0
        self._do_test(dict(default_nonmember_action=Action.accept))

    def test_nonmember_hold(self):
        self._pckdict['generic_nonmember_action'] = 1
        self._do_test(dict(default_nonmember_action=Action.hold))

    def test_nonmember_reject(self):
        self._pckdict['generic_nonmember_action'] = 2
        self._do_test(dict(default_nonmember_action=Action.reject))

    def test_nonmember_discard(self):
        self._pckdict['generic_nonmember_action'] = 3
        self._do_test(dict(default_nonmember_action=Action.discard))


class TestConvertToURI(unittest.TestCase):
    # The following values were plain text, and are now URIs in Mailman 3:
    # - welcome_message_uri
    # - goodbye_message_uri
    # - header_uri
    # - footer_uri
    # - digest_header_uri
    # - digest_footer_uri
    #
    # The templates contain variables that must be replaced:
    # - %(real_name)s -> %(display_name)s
    # - %(real_name)s@%(host_name)s -> %(fqdn_listname)s
    # - %(web_page_url)slistinfo%(cgiext)s/%(_internal_name)s
    #       -> %(listinfo_uri)s

    layer = ConfigLayer
    maxDiff = None

    def setUp(self):
        self._mlist = create_list('blank@example.com')
        self._conf_mapping = dict(
            welcome_msg='list:user:notice:welcome',
            goodbye_msg='list:user:notice:goodbye',
            msg_header='list:member:regular:header',
            msg_footer='list:member:regular:footer',
            digest_header='list:member:digest:header',
            digest_footer='list:member:digest:footer',
            )
        self._pckdict = dict()

    def test_text_to_uri(self):
        for oldvar, newvar in self._conf_mapping.items():
            self._pckdict[str(oldvar)] = b'TEST VALUE'
            import_config_pck(self._mlist, self._pckdict)
            text = decorate(newvar, self._mlist)
            self.assertEqual(
                text, 'TEST VALUE',
                'Old variable %s was not properly imported to %s'
                % (oldvar, newvar))

    def test_substitutions(self):
        test_text = ('UNIT TESTING %(real_name)s mailing list\n'
                     '%(real_name)s@%(host_name)s')
        expected_text = ('UNIT TESTING $display_name mailing list '
                         '-- $listname\n'
                         'To unsubscribe send an email to '
                         '${short_listname}-leave@${domain}')
        for oldvar, newvar in self._conf_mapping.items():
            self._pckdict[str(oldvar)] = str(test_text)
            import_config_pck(self._mlist, self._pckdict)
            text = getUtility(ITemplateLoader).get(newvar, self._mlist)
            self.assertEqual(
                text, expected_text,
                'Old variables were not converted for %s' % newvar)

    def test_keep_default(self):
        # If the value was not changed from MM2.1's default, don't import it.
        default_msg_footer = (
            '_______________________________________________\n'
            '%(real_name)s mailing list\n'
            '%(real_name)s@%(host_name)s\n'
            '%(web_page_url)slistinfo%(cgiext)s/%(_internal_name)s\n'
            )
        loader = getUtility(ITemplateLoader)
        for oldvar in ('msg_footer', 'digest_footer'):
            newvar = self._conf_mapping[oldvar]
            self._pckdict[str(oldvar)] = str(default_msg_footer)
            try:
                old_value = loader.get(newvar, self._mlist)
            except URLError:
                old_value = None
            import_config_pck(self._mlist, self._pckdict)
            try:
                new_value = loader.get(newvar, self._mlist)
            except URLError:
                new_value = None
            self.assertEqual(
                old_value, new_value,
                '{} changed unexpectedly: {} != {}'.format(
                    newvar, old_value, new_value))

    def test_keep_default_if_fqdn_changed(self):
        # Use case: importing the old a@ex.com into b@ex.com.  We can't check
        # if it changed from the default so don't import.  We may do more harm
        # than good and it's easy to change if needed.
        test_value = b'TEST-VALUE'
        # We need an IDomain for this mail_host.
        getUtility(IDomainManager).add('test.example.com')
        manager = getUtility(ITemplateManager)
        for oldvar, newvar in self._conf_mapping.items():
            self._mlist.mail_host = 'example.com'
            self._pckdict['mail_host'] = b'test.example.com'
            self._pckdict[str(oldvar)] = test_value
            try:
                old_value = manager.get(newvar, 'blank.example.com')
            except URLError:
                old_value = None
            # Suppress warning messages in the test output.
            with mock.patch('sys.stderr'):
                import_config_pck(self._mlist, self._pckdict)
            try:
                new_value = manager.get(newvar, 'test.example.com')
            except URLError:
                new_value = None
            self.assertEqual(
                old_value, new_value,
                '{} changed unexpectedly: {} != {}'.format(
                    newvar, old_value, new_value))

    def test_unicode(self):
        # non-ascii templates
        for oldvar in self._conf_mapping:
            self._pckdict[str(oldvar)] = b'Ol\xe1!'
        import_config_pck(self._mlist, self._pckdict)
        for oldvar, newvar in self._conf_mapping.items():
            text = decorate(newvar, self._mlist)
            expected = u'Ol\ufffd!'
            self.assertEqual(
                text, expected,
                '{} -> {} did not get converted'.format(oldvar, newvar))

    def test_unicode_in_default(self):
        # What if the default template is already in UTF-8?   For example, if
        # you import it twice.
        footer = b'\xe4\xb8\xad $listinfo_uri'
        footer_path = os.path.join(
            config.VAR_DIR, 'templates', 'lists',
            'blank@example.com', 'en', 'footer.txt')
        makedirs(os.path.dirname(footer_path))
        with open(footer_path, 'wb') as fp:
            fp.write(footer)
        self._pckdict['msg_footer'] = b'NEW-VALUE'
        import_config_pck(self._mlist, self._pckdict)
        text = decorate('list:member:regular:footer', self._mlist)
        self.assertEqual(text, 'NEW-VALUE')


class TestRosterImport(unittest.TestCase):
    """Test that rosters are imported correctly."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('blank@example.com')
        self._pckdict = {
            'members': {
                'anne@example.com': 0,
                'bob@example.com': b'bob@ExampLe.Com',
                },
            'digest_members': {
                'cindy@example.com': 0,
                'dave@example.com': b'dave@ExampLe.Com',
                },
            'passwords': {
                'anne@example.com': b'annepass',
                'bob@example.com': b'bobpass',
                'cindy@example.com': b'cindypass',
                'dave@example.com': b'davepass',
                },
            'language': {
                'anne@example.com': b'fr',
                'bob@example.com': b'de',
                'cindy@example.com': b'es',
                'dave@example.com': b'it',
                },
            # Usernames are unicode strings in the pickle
            'usernames': {
                'anne@example.com': 'Anne',
                'bob@example.com': 'Bob',
                'cindy@example.com': 'Cindy',
                'dave@example.com': 'Dave',
                },
            'owner': [
                'anne@example.com',
                'emily@example.com',
                ],
            'moderator': [
                'bob@example.com',
                'fred@example.com',
                ],
            'accept_these_nonmembers': [
                'gene@example.com',
                '^gene-.*@example.com',
                ],
            'hold_these_nonmembers': [
                'homer@example.com',
                '^homer-.*@example.com',
                ],
            'reject_these_nonmembers': [
                'iris@example.com',
                '^iris-.*@example.com',
                ],
            'discard_these_nonmembers': [
                'kenny@example.com',
                '^kenny-.*@example.com',
                ],
            }
        self._usermanager = getUtility(IUserManager)
        language_manager = getUtility(ILanguageManager)
        for code in self._pckdict['language'].values():
            if isinstance(code, bytes):
                code = code.decode('utf-8')
            if code not in language_manager.codes:
                language_manager.add(code, 'utf-8', code)

    def test_member(self):
        import_config_pck(self._mlist, self._pckdict)
        for name in ('anne', 'bob', 'cindy', 'dave'):
            addr = '%s@example.com' % name
            self.assertIn(addr,
                          [a.email for a in self._mlist.members.addresses],
                          'Address %s was not imported' % addr)
        self.assertIn('anne@example.com',
                      [a.email for a in self._mlist.regular_members.addresses])
        self.assertIn('bob@example.com',
                      [a.email for a in self._mlist.regular_members.addresses])
        self.assertIn('cindy@example.com',
                      [a.email for a in self._mlist.digest_members.addresses])
        self.assertIn('dave@example.com',
                      [a.email for a in self._mlist.digest_members.addresses])

    def test_original_email(self):
        import_config_pck(self._mlist, self._pckdict)
        bob = self._usermanager.get_address('bob@example.com')
        self.assertEqual(bob.original_email, 'bob@ExampLe.Com')
        dave = self._usermanager.get_address('dave@example.com')
        self.assertEqual(dave.original_email, 'dave@ExampLe.Com')

    def test_language(self):
        import_config_pck(self._mlist, self._pckdict)
        for name in ('anne', 'bob', 'cindy', 'dave'):
            addr = '%s@example.com' % name
            member = self._mlist.members.get_member(addr)
            self.assertIsNotNone(member, 'Address %s was not imported' % addr)
            code = self._pckdict['language'][addr]
            if isinstance(code, bytes):
                code = code.decode('utf-8')
            self.assertEqual(member.preferred_language.code, code)

    def test_new_language(self):
        self._pckdict['language']['anne@example.com'] = b'xx_XX'
        try:
            import_config_pck(self._mlist, self._pckdict)
        except Import21Error as error:
            self.assertIn('[language.xx_XX]', str(error))
        else:
            self.fail('Import21Error was not raised')

    def test_username(self):
        import_config_pck(self._mlist, self._pckdict)
        for name in ('anne', 'bob', 'cindy', 'dave'):
            addr = '%s@example.com' % name
            user = self._usermanager.get_user(addr)
            address = self._usermanager.get_address(addr)
            self.assertIsNotNone(user, 'User %s was not imported' % addr)
            self.assertIsNotNone(address, 'Address %s was not imported' % addr)
            display_name = self._pckdict['usernames'][addr]
            self.assertEqual(
                user.display_name, display_name,
                'The display name was not set for User %s' % addr)
            self.assertEqual(
                address.display_name, display_name,
                'The display name was not set for Address %s' % addr)

    def test_owner(self):
        import_config_pck(self._mlist, self._pckdict)
        for name in ('anne', 'emily'):
            addr = '%s@example.com' % name
            self.assertIn(addr,
                          [a.email for a in self._mlist.owners.addresses],
                          'Address %s was not imported as owner' % addr)
        self.assertNotIn(
            'emily@example.com',
            [a.email for a in self._mlist.members.addresses],
            'Address emily@ was wrongly added to the members list')

    def test_moderator(self):
        import_config_pck(self._mlist, self._pckdict)
        for name in ('bob', 'fred'):
            addr = '%s@example.com' % name
            self.assertIn(addr,
                          [a.email for a in self._mlist.moderators.addresses],
                          'Address %s was not imported as moderator' % addr)
        self.assertNotIn('fred@example.com',
                         [a.email for a in self._mlist.members.addresses],
                         'Address fred@ was wrongly added to the members list')

    def test_password(self):
        # self.anne.password = config.password_context.encrypt('abc123')
        import_config_pck(self._mlist, self._pckdict)
        for name in ('anne', 'bob', 'cindy', 'dave'):
            addr = '%s@example.com' % name
            user = self._usermanager.get_user(addr)
            self.assertIsNotNone(user, 'Address %s was not imported' % addr)
            self.assertEqual(
                user.password, '{plaintext}%spass' % name,
                'Password for %s was not imported' % addr)

    def test_same_user(self):
        # Adding the address of an existing User must not create another user.
        user = self._usermanager.create_user('anne@example.com', 'Anne')
        user.register('bob@example.com')                   # secondary email
        import_config_pck(self._mlist, self._pckdict)
        member = self._mlist.members.get_member('bob@example.com')
        self.assertEqual(member.user, user)

    def test_owner_and_moderator_not_lowercase(self):
        # In the v2.1 pickled dict, the owner and moderator lists are not
        # necessarily lowercased already.
        self._pckdict['owner'] = [b'Anne@example.com']
        self._pckdict['moderator'] = [b'Anne@example.com']
        import_config_pck(self._mlist, self._pckdict)
        self.assertIn('anne@example.com',
                      [a.email for a in self._mlist.owners.addresses])
        self.assertIn('anne@example.com',
                      [a.email for a in self._mlist.moderators.addresses])

    def test_address_already_exists_but_no_user(self):
        # An address already exists, but it is not linked to a user nor
        # subscribed.
        anne_addr = self._usermanager.create_address(
            'anne@example.com', 'Anne')
        import_config_pck(self._mlist, self._pckdict)
        anne = self._usermanager.get_user('anne@example.com')
        self.assertTrue(anne.controls('anne@example.com'))
        self.assertIn(anne_addr, self._mlist.regular_members.addresses)

    def test_address_already_subscribed_but_no_user(self):
        # An address is already subscribed, but it is not linked to a user.
        anne_addr = self._usermanager.create_address(
            'anne@example.com', 'Anne')
        self._mlist.subscribe(anne_addr)
        # Suppress warning messages in test output.
        with mock.patch('sys.stderr'):
            import_config_pck(self._mlist, self._pckdict)
        anne = self._usermanager.get_user('anne@example.com')
        self.assertTrue(anne.controls('anne@example.com'))

    def test_invalid_original_email(self):
        # When the member has an original email address (i.e. the
        # case-preserved version) that is invalid, their new address record's
        # original_email attribute will only be the case insensitive version.
        self._pckdict['members']['anne@example.com'] = b'invalid email address'
        try:
            import_config_pck(self._mlist, self._pckdict)
        except InvalidEmailAddressError as error:
            self.fail(error)
        self.assertIn('anne@example.com',
                      [a.email for a in self._mlist.members.addresses])
        anne = self._usermanager.get_address('anne@example.com')
        self.assertEqual(anne.original_email, 'anne@example.com')

    def test_invalid_email(self):
        # When a member's email address is invalid, that member is skipped
        # during the import.
        self._pckdict['members'] = {
            'anne@example.com': 0,
            'invalid email address': b'invalid email address'
            }
        self._pckdict['digest_members'] = {}
        try:
            import_config_pck(self._mlist, self._pckdict)
        except InvalidEmailAddressError as error:
            self.fail(error)
        self.assertEqual(['anne@example.com'],
                         [a.email for a in self._mlist.members.addresses])

    def test_no_email_sent(self):
        # No welcome message is sent to newly imported members.
        self.assertTrue(self._mlist.send_welcome_message)
        import_config_pck(self._mlist, self._pckdict)
        self.assertIn('anne@example.com',
                      [a.email for a in self._mlist.members.addresses])
        # There are no messages in any of the queues.
        for queue, switchboard in config.switchboards.items():
            file_count = len(switchboard.files)
            self.assertEqual(file_count, 0,
                             "Unexpected queue '{}' file count: {}".format(
                                 queue, file_count))
        self.assertTrue(self._mlist.send_welcome_message)

    def test_nonmembers(self):
        import_config_pck(self._mlist, self._pckdict)
        expected = {
            'gene': Action.accept,
            'homer': Action.hold,
            'iris': Action.reject,
            'kenny': Action.discard,
            }
        for name, action in expected.items():
            self.assertIn('{}@example.com'.format(name),
                          [a.email for a in self._mlist.nonmembers.addresses],
                          'Address {} was not imported'.format(name))
            member = self._mlist.nonmembers.get_member(
                '{}@example.com'.format(name))
            self.assertEqual(member.moderation_action, action)
            # Only regexps should remain in the list property.
            list_prop = getattr(
                self._mlist,
                '{}_these_nonmembers'.format(action.name))
            self.assertEqual(len(list_prop), 1)
            self.assertTrue(all(addr.startswith('^') for addr in list_prop))


class TestPreferencesImport(unittest.TestCase):
    """Preferences get imported too."""

    layer = ConfigLayer

    def setUp(self):
        self._mlist = create_list('blank@example.com')
        self._pckdict = dict(
            members={'anne@example.com': 0},
            user_options=dict(),
            delivery_status=dict(),
            )
        self._usermanager = getUtility(IUserManager)

    def _do_test(self, oldvalue, expected):
        self._pckdict['user_options']['anne@example.com'] = oldvalue
        import_config_pck(self._mlist, self._pckdict)
        user = self._usermanager.get_user('anne@example.com')
        self.assertIsNotNone(user, 'User was not imported')
        member = self._mlist.members.get_member('anne@example.com')
        self.assertIsNotNone(member, 'Address was not subscribed')
        for exp_name, exp_val in expected.items():
            try:
                currentval = getattr(member, exp_name)
            except AttributeError:
                # hide_address has no direct getter
                currentval = getattr(member.preferences, exp_name)
            self.assertEqual(
                currentval, exp_val,
                'Preference %s was not imported' % exp_name)
        # XXX: should I check that other params are still equal to
        # mailman.core.constants.system_preferences?

    def test_acknowledge_posts(self):
        # AcknowledgePosts
        self._do_test(4, dict(acknowledge_posts=True))

    def test_hide_address(self):
        # ConcealSubscription
        self._do_test(16, dict(hide_address=True))

    def test_receive_own_postings(self):
        # DontReceiveOwnPosts
        self._do_test(2, dict(receive_own_postings=False))

    def test_receive_list_copy(self):
        # DontReceiveDuplicates
        self._do_test(256, dict(receive_list_copy=False))

    def test_digest_plain(self):
        # Digests & DisableMime
        self._pckdict['digest_members'] = self._pckdict['members'].copy()
        self._pckdict['members'] = dict()
        self._do_test(8, dict(delivery_mode=DeliveryMode.plaintext_digests))

    def test_digest_mime(self):
        # Digests & not DisableMime
        self._pckdict['digest_members'] = self._pckdict['members'].copy()
        self._pckdict['members'] = dict()
        self._do_test(0, dict(delivery_mode=DeliveryMode.mime_digests))

    def test_delivery_status(self):
        # Look for the pckdict['delivery_status'] key which will look like
        # (status, time) where status is among the following:
        # ENABLED  = 0 # enabled
        # UNKNOWN  = 1 # legacy disabled
        # BYUSER   = 2 # disabled by user choice
        # BYADMIN  = 3 # disabled by admin choice
        # BYBOUNCE = 4 # disabled by bounces
        for oldval, expected in enumerate((
                DeliveryStatus.enabled,
                DeliveryStatus.unknown, DeliveryStatus.by_user,
                DeliveryStatus.by_moderator, DeliveryStatus.by_bounces)):
            self._pckdict['delivery_status']['anne@example.com'] = (oldval, 0)
            import_config_pck(self._mlist, self._pckdict)
            member = self._mlist.members.get_member('anne@example.com')
            self.assertIsNotNone(member, 'Address was not subscribed')
            self.assertEqual(member.delivery_status, expected)
            member.unsubscribe()

    def test_moderate_hold(self):
        # Option flag Moderate is translated to the action set in
        # member_moderation_action.
        self._pckdict['member_moderation_action'] = 0
        self._do_test(128, dict(moderation_action=Action.hold))

    def test_moderate_reject(self):
        # Option flag Moderate is translated to the action set in
        # member_moderation_action.
        self._pckdict['member_moderation_action'] = 1
        self._do_test(128, dict(moderation_action=Action.reject))

    def test_moderate_hold_discard(self):
        # Option flag Moderate is translated to the action set in
        # member_moderation_action.
        self._pckdict['member_moderation_action'] = 2
        self._do_test(128, dict(moderation_action=Action.discard))

    def test_no_moderate(self):
        # If the option flag Moderate is not set, the action is defer.
        # See: https://gitlab.com/mailman/mailman/merge_requests/100
        self._pckdict['member_moderation_action'] = 1          # reject
        self._do_test(0, dict(moderation_action=Action.defer))

    def test_multiple_options(self):
        # DontReceiveDuplicates & DisableMime & SuppressPasswordReminder
        # Keys might be Python 2 str/bytes or unicode.
        members = self._pckdict['members']
        self._pckdict['digest_members'] = members.copy()
        self._pckdict['members'] = dict()
        self._do_test(296, dict(
                receive_list_copy=False,
                delivery_mode=DeliveryMode.plaintext_digests,
                ))

    def test_language_code_none(self):
        self.assertIsNone(check_language_code(None))
