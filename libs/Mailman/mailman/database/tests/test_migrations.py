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

"""Test database schema migrations with Alembic"""

import os
import unittest
import sqlalchemy as sa
import alembic.command

from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.database.alembic import alembic_cfg
from mailman.database.helpers import exists_in_db
from mailman.database.model import Model
from mailman.database.transaction import transaction
from mailman.database.types import Enum, SAUnicode
from mailman.interfaces.action import Action
from mailman.interfaces.cache import ICacheManager
from mailman.interfaces.member import MemberRole
from mailman.interfaces.template import ITemplateManager
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.layers import ConfigLayer
from zope.component import getUtility


class TestMigrations(unittest.TestCase):
    layer = ConfigLayer

    def setUp(self):
        alembic.command.stamp(alembic_cfg, 'head')

    def tearDown(self):
        # Drop and restore a virgin database.
        config.db.store.rollback()
        md = sa.MetaData(bind=config.db.engine)
        md.reflect()
        # We have circular dependencies between user and address, thus we can't
        # use drop_all() without getting a warning.  Setting use_alter to True
        # on the foreign keys helps SQLAlchemy mark those loops as known.
        for tablename in ('user', 'address'):
            if tablename not in md.tables:
                continue
            for fk in md.tables[tablename].foreign_keys:
                fk.constraint.use_alter = True
        md.drop_all()
        Model.metadata.create_all(config.db.engine)

    def test_all_migrations(self):
        script_dir = alembic.script.ScriptDirectory.from_config(alembic_cfg)
        revisions = [sc.revision for sc in script_dir.walk_revisions()]
        for revision in revisions:
            alembic.command.downgrade(alembic_cfg, revision)
        revisions.reverse()
        for revision in revisions:
            alembic.command.upgrade(alembic_cfg, revision)

    def test_42756496720_header_matches(self):
        test_header_matches = [
            ('test-header-1', 'test-pattern-1'),
            ('test-header-2', 'test-pattern-2'),
            ('test-header-3', 'test-pattern-3'),
            ]
        mlist_table = sa.sql.table(
            'mailinglist',
            sa.sql.column('id', sa.Integer),
            sa.sql.column('header_matches', sa.PickleType)
            )
        header_match_table = sa.sql.table(
            'headermatch',
            sa.sql.column('mailing_list_id', sa.Integer),
            sa.sql.column('header', SAUnicode),
            sa.sql.column('pattern', SAUnicode),
            )
        # Bring the DB to the revision that is being tested.
        alembic.command.downgrade(alembic_cfg, '42756496720')
        # Test downgrading.
        config.db.store.execute(mlist_table.insert().values(id=1))
        config.db.store.execute(header_match_table.insert().values(
            [{'mailing_list_id': 1, 'header': hm[0], 'pattern': hm[1]}
             for hm in test_header_matches]))
        config.db.store.commit()
        alembic.command.downgrade(alembic_cfg, '2bb9b382198')
        results = config.db.store.execute(
            mlist_table.select()).fetchall()
        self.assertEqual(results[0].header_matches, test_header_matches)
        self.assertFalse(exists_in_db(config.db.engine, 'headermatch'))
        config.db.store.commit()
        # Test upgrading.
        alembic.command.upgrade(alembic_cfg, '42756496720')
        results = config.db.store.execute(
            header_match_table.select()).fetchall()
        self.assertEqual(
            results,
            [(1, hm[0], hm[1]) for hm in test_header_matches])

    def test_47294d3a604_pendable_keyvalues(self):
        # We have 5 pended items:
        # - one is a probe request
        # - one is a subscription request
        # - one is a moderation request
        # - one is a held message
        # - one is a registration request in the new format
        #
        # The first three used to have no 'type' key and must be properly
        # typed, the held message used to have a type key, but in JSON, and
        # must be converted.
        pended_table = sa.sql.table(
            'pended',
            sa.sql.column('id', sa.Integer),
            )
        keyvalue_table = sa.sql.table(
            'pendedkeyvalue',
            sa.sql.column('id', sa.Integer),
            sa.sql.column('key', SAUnicode),
            sa.sql.column('value', SAUnicode),
            sa.sql.column('pended_id', sa.Integer),
            )
        def get_from_db():                                 # noqa: E306
            results = {}
            for i in range(1, 6):
                query = sa.sql.select(
                    [keyvalue_table.c.key, keyvalue_table.c.value]
                    ).where(
                        keyvalue_table.c.pended_id == i
                    )
                results[i] = dict([
                    (r['key'], r['value']) for r in
                    config.db.store.execute(query).fetchall()
                    ])
            return results
        # Start at the previous revision
        with transaction():
            alembic.command.downgrade(alembic_cfg, '33bc0099223')
            for i in range(1, 6):
                config.db.store.execute(pended_table.insert().values(id=i))
            config.db.store.execute(keyvalue_table.insert().values([
                {'pended_id': 1, 'key': 'member_id', 'value': 'test-value'},
                {'pended_id': 2, 'key': 'token_owner', 'value': 'test-value'},
                {'pended_id': 3, 'key': '_mod_message_id',
                                 'value': 'test-value'},
                {'pended_id': 4, 'key': 'type', 'value': '"held message"'},
                {'pended_id': 5, 'key': 'type', 'value': 'registration'},
                ]))
        # Upgrading.
        with transaction():
            alembic.command.upgrade(alembic_cfg, '47294d3a604')
            results = get_from_db()
        for i in range(1, 5):
            self.assertIn('type', results[i])
        self.assertEqual(results[1]['type'], 'probe')
        self.assertEqual(results[2]['type'], 'subscription')
        self.assertEqual(results[3]['type'], 'data')
        self.assertEqual(results[4]['type'], 'held message')
        self.assertEqual(results[5]['type'], 'registration')
        # Downgrading.
        with transaction():
            alembic.command.downgrade(alembic_cfg, '33bc0099223')
            results = get_from_db()
        for i in range(1, 4):
            self.assertNotIn('type', results[i])
        self.assertEqual(results[4]['type'], '"held message"')
        self.assertEqual(results[5]['type'], '"registration"')

    def test_70af5a4e5790_digests(self):
        IDS_TO_DIGESTABLE = [
            (1, True),
            (2, False),
            (3, False),
            (4, True),
            ]
        mlist_table = sa.sql.table(
            'mailinglist',
            sa.sql.column('id', sa.Integer),
            sa.sql.column('digests_enabled', sa.Boolean)
            )
        # Downgrading.
        with transaction():
            for table_id, enabled in IDS_TO_DIGESTABLE:
                config.db.store.execute(mlist_table.insert().values(
                    id=table_id, digests_enabled=enabled))
        with transaction():
            alembic.command.downgrade(alembic_cfg, '47294d3a604')
            results = config.db.store.execute(
                'SELECT id, digestable FROM mailinglist').fetchall()
        self.assertEqual(results, IDS_TO_DIGESTABLE)
        # Upgrading.
        with transaction():
            alembic.command.upgrade(alembic_cfg, '70af5a4e5790')
        results = config.db.store.execute(
            'SELECT id, digests_enabled FROM mailinglist').fetchall()
        self.assertEqual(results, IDS_TO_DIGESTABLE)

    def test_70af5a4e5790_data_paths(self):
        # Create a couple of mailing lists through the standard API.
        with transaction():
            create_list('ant@example.com')
            create_list('bee@example.com')
        # Downgrade and verify that the old data paths exist.
        alembic.command.downgrade(alembic_cfg, '47294d3a604')
        self.assertTrue(os.path.exists(
            os.path.join(config.LIST_DATA_DIR, 'ant@example.com')))
        self.assertTrue(os.path.exists(
            os.path.join(config.LIST_DATA_DIR, 'ant@example.com')))
        # Upgrade and verify that the new data paths exists and the old ones
        # no longer do.
        alembic.command.upgrade(alembic_cfg, '70af5a4e5790')
        self.assertFalse(os.path.exists(
            os.path.join(config.LIST_DATA_DIR, 'ant@example.com')))
        self.assertFalse(os.path.exists(
            os.path.join(config.LIST_DATA_DIR, 'bee@example.com')))
        self.assertTrue(os.path.exists(
            os.path.join(config.LIST_DATA_DIR, 'ant.example.com')))
        self.assertTrue(os.path.exists(
            os.path.join(config.LIST_DATA_DIR, 'bee.example.com')))

    def test_7b254d88f122_moderation_action(self):
        # Create a mailing list through the standard API.
        with transaction():
            ant = create_list('ant@example.com')
            default_member_action = ant.default_member_action
            default_nonmember_action = ant.default_nonmember_action
        sa.sql.table(
            'mailinglist',
            sa.sql.column('id', sa.Integer),
            sa.sql.column('list_id', SAUnicode),
            sa.sql.column('default_member_action', Enum(Action)),
            sa.sql.column('default_nonmember_action', Enum(Action)),
            )
        member_table = sa.sql.table(
            'member',
            sa.sql.column('id', sa.Integer),
            sa.sql.column('list_id', SAUnicode),
            sa.sql.column('address_id', sa.Integer),
            sa.sql.column('role', Enum(MemberRole)),
            sa.sql.column('moderation_action', Enum(Action)),
            )
        user_manager = getUtility(IUserManager)
        with transaction():
            # Start at the previous revision.
            alembic.command.downgrade(alembic_cfg, 'd4fbb4fd34ca')
            # Create some members.
            anne = user_manager.create_address('anne@example.com')
            bart = user_manager.create_address('bart@example.com')
            cris = user_manager.create_address('cris@example.com')
            dana = user_manager.create_address('dana@example.com')
            # Flush the database to get the last auto-increment id.
            config.db.store.flush()
            # Assign some moderation actions to the members created above.
            config.db.store.execute(member_table.insert().values([
                {'address_id': anne.id, 'role': MemberRole.owner,
                 'list_id': 'ant.example.com',
                 'moderation_action': Action.accept},
                {'address_id': bart.id, 'role': MemberRole.moderator,
                 'list_id': 'ant.example.com',
                 'moderation_action': Action.accept},
                {'address_id': cris.id, 'role': MemberRole.member,
                 'list_id': 'ant.example.com',
                 'moderation_action': Action.defer},
                {'address_id': dana.id, 'role': MemberRole.nonmember,
                 'list_id': 'ant.example.com',
                 'moderation_action': Action.hold},
                ]))
        # Cris and Dana have actions which match the list default action for
        # members and nonmembers respectively.
        query = sa.sql.select([member_table.c.moderation_action]).where(
            sa.and_(
                member_table.c.role == MemberRole.member,
                member_table.c.list_id == 'ant.example.com',
                # cris@example.com
                member_table.c.address_id == 3,
                )
            )
        action = config.db.store.execute(query).fetchone()[0]
        self.assertEqual(action, default_member_action)
        query = sa.sql.select([member_table.c.moderation_action]).where(
            sa.and_(
                member_table.c.role == MemberRole.nonmember,
                member_table.c.list_id == 'ant.example.com',
                # dana@example.com
                member_table.c.address_id == 4,
                )
            )
        action = config.db.store.execute(query).fetchone()[0]
        self.assertEqual(action, default_nonmember_action)
        # Upgrade and check the moderation_actions.   Cris's and Dana's
        # actions have been set to None to fall back to the list defaults.
        alembic.command.upgrade(alembic_cfg, '7b254d88f122')
        members = config.db.store.execute(sa.select([
            member_table.c.address_id, member_table.c.moderation_action,
            ])).fetchall()
        self.assertEqual(members, [
            (anne.id, Action.accept),
            (bart.id, Action.accept),
            (cris.id, None),
            (dana.id, None),
            ])
        # Downgrade and check that Cris's and Dana's actions have been set
        # explicitly.
        alembic.command.downgrade(alembic_cfg, 'd4fbb4fd34ca')
        members = config.db.store.execute(sa.select([
            member_table.c.address_id, member_table.c.moderation_action,
            ])).fetchall()
        self.assertEqual(members, [
            (anne.id, Action.accept),
            (bart.id, Action.accept),
            (cris.id, Action.defer),
            (dana.id, Action.hold),
            ])

    def test_fa0d96e28631_upgrade_uris(self):
        mlist_table = sa.sql.table(
            'mailinglist',
            sa.sql.column('id', sa.Integer),
            sa.sql.column('list_id', sa.Unicode),
            sa.sql.column('digest_footer_uri', sa.Unicode),
            sa.sql.column('digest_header_uri', sa.Unicode),
            sa.sql.column('footer_uri', sa.Unicode),
            sa.sql.column('header_uri', sa.Unicode),
            sa.sql.column('goodbye_message_uri', sa.Unicode),
            sa.sql.column('welcome_message_uri', sa.Unicode),
            )
        with transaction():
            # Start at the previous revision.
            alembic.command.downgrade(alembic_cfg, '7b254d88f122')
            # Create a mailing list with some URIs.
            config.db.store.execute(mlist_table.insert().values(
                list_id='ant.example.com',
                digest_footer_uri='mailman:///digest_footer.txt',
                digest_header_uri='mailman:///digest_header.txt',
                footer_uri='mailman:///footer.txt',
                header_uri='mailman:///header.txt',
                goodbye_message_uri='mailman:///goodbye.txt',
                welcome_message_uri='mailman:///welcome.txt',
                ))
        # Now upgrade and check to see if the values got into the template
        # table correctly.
        alembic.command.upgrade(alembic_cfg, 'fa0d96e28631')
        seen_names = []
        template_table = sa.sql.table(
            'template',
            sa.sql.column('id', sa.Integer),
            sa.sql.column('name', sa.Unicode),
            sa.sql.column('context', sa.Unicode),
            sa.sql.column('uri', sa.Unicode),
            sa.sql.column('username', sa.Unicode),
            sa.sql.column('password', sa.DateTime),
            )
        for (table_id, name, context, uri,
             username, password) in config.db.store.execute(
                 template_table.select()):
            # This information isn't available in the old database
            # version, so there's no way these can be set.
            seen_names.append(name)
            self.assertIsNone(username)
            self.assertIsNone(password)
            self.assertEqual(context, 'ant.example.com')
            self.assertEqual(uri, 'mailman:///{}.txt'.format({
                'list:digest:footer': 'digest_footer',
                'list:digest:header': 'digest_header',
                'list:regular:footer': 'footer',
                'list:regular:header': 'header',
                'list:user:notice:goodbye': 'goodbye',
                'list:user:notice:welcome': 'welcome',
                }.get(name, name)))
        self.assertEqual(sorted(seen_names), [
            'list:digest:footer',
            'list:digest:header',
            'list:regular:footer',
            'list:regular:header',
            'list:user:notice:goodbye',
            'list:user:notice:welcome',
            ])

    def test_fa0d96e28631_upgrade_no_uris(self):
        mlist_table = sa.sql.table(
            'mailinglist',
            sa.sql.column('id', sa.Integer),
            sa.sql.column('list_id', sa.Unicode),
            sa.sql.column('digest_footer_uri', sa.Unicode),
            sa.sql.column('digest_header_uri', sa.Unicode),
            sa.sql.column('footer_uri', sa.Unicode),
            sa.sql.column('header_uri', sa.Unicode),
            sa.sql.column('goodbye_message_uri', sa.Unicode),
            sa.sql.column('welcome_message_uri', sa.Unicode),
            )
        # None of the URL parameters are defined.
        with transaction():
            # Start at the previous revision.
            alembic.command.downgrade(alembic_cfg, '7b254d88f122')
            # Create a mailing list without any URLs.
            config.db.store.execute(mlist_table.insert().values(
                list_id='ant.example.com'))
        # Now upgrade.  There are no templates.
        alembic.command.upgrade(alembic_cfg, 'fa0d96e28631')
        template_table = sa.sql.table(
            'template',
            sa.sql.column('id', sa.Integer),
            )
        entries = list(config.db.store.execute(template_table.select()))
        self.assertEqual(len(entries), 0)

    def test_fa0d96e28631_downgrade_uris(self):
        # Create some cache directory entries.
        self.assertTrue(os.path.exists(config.CACHE_DIR))
        getUtility(ICacheManager).add('abc', 'def')
        self.assertNotEqual(len(os.listdir(config.CACHE_DIR)), 0)
        # Set up the templates using the current API.
        with transaction():
            create_list('ant@example.com')
            manager = getUtility(ITemplateManager)
            manager.set('list:digest:footer',
                        'ant.example.com',
                        'mailman:///digest_footer.txt')
            manager.set('list:digest:header',
                        'ant.example.com',
                        'mailman:///digest_header.txt')
            manager.set('list:regular:footer',
                        'ant.example.com',
                        'mailman:///footer.txt')
            manager.set('list:regular:header',
                        'ant.example.com',
                        'mailman:///header.txt')
            manager.set('list:user:notice:welcome',
                        'ant.example.com',
                        'mailman:///welcome.txt')
            manager.set('list:user:notice:goodbye',
                        'ant.example.com',
                        'mailman:///goodbye.txt')
        mlist_table = sa.sql.table(
            'mailinglist',
            sa.sql.column('id', sa.Integer),
            sa.sql.column('list_id', sa.Unicode),
            sa.sql.column('digest_footer_uri', sa.Unicode),
            sa.sql.column('digest_header_uri', sa.Unicode),
            sa.sql.column('footer_uri', sa.Unicode),
            sa.sql.column('header_uri', sa.Unicode),
            sa.sql.column('goodbye_message_uri', sa.Unicode),
            sa.sql.column('welcome_message_uri', sa.Unicode),
            )
        alembic.command.downgrade(alembic_cfg, '7b254d88f122')
        for (table_id, list_id, digest_footer_uri, digest_header_uri,
             footer_uri, header_uri,
             goodbye_message_uri,
             welcome_message_uri) in config.db.store.execute(
                 mlist_table.select()):
            self.assertEqual(list_id, 'ant.example.com')
            self.assertEqual(digest_footer_uri, 'mailman:///digest_footer.txt')
            self.assertEqual(digest_header_uri, 'mailman:///digest_header.txt')
            self.assertEqual(footer_uri, 'mailman:///footer.txt')
            self.assertEqual(header_uri, 'mailman:///header.txt')
            self.assertEqual(welcome_message_uri, 'mailman:///welcome.txt')
            self.assertEqual(goodbye_message_uri, 'mailman:///goodbye.txt')
        # The cache directories are gone too.
        self.assertEqual(len(os.listdir(config.CACHE_DIR)), 0,
                         os.listdir(config.CACHE_DIR))

    def test_fa0d96e28631_downgrade_missing_list(self):
        with transaction():
            manager = getUtility(ITemplateManager)
            manager.set('list:regular:footer',
                        'missing.example.com',
                        'mailman:///missing-footer.txt')
        alembic.command.downgrade(alembic_cfg, '7b254d88f122')
        mlist_table = sa.sql.table(
            'mailinglist',
            sa.sql.column('id', sa.Integer),
            sa.sql.column('footer_uri', sa.Unicode),
            )
        self.assertEqual(
            len(list(config.db.store.execute(mlist_table.select()))),
            0)
