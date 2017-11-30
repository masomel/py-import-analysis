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

"""Importer routines."""

import os
import re
import sys
import logging
import datetime

from mailman.config import config
from mailman.handlers.decorate import decorate_template
from mailman.interfaces.action import Action, FilterAction
from mailman.interfaces.address import IEmailValidator
from mailman.interfaces.archiver import ArchivePolicy
from mailman.interfaces.autorespond import ResponseAction
from mailman.interfaces.bans import IBanManager
from mailman.interfaces.bounce import UnrecognizedBounceDisposition
from mailman.interfaces.digests import DigestFrequency
from mailman.interfaces.errors import MailmanError
from mailman.interfaces.languages import ILanguageManager
from mailman.interfaces.mailinglist import (
    IAcceptableAliasSet, IHeaderMatchList, Personalization, ReplyToMunging,
    SubscriptionPolicy)
from mailman.interfaces.member import DeliveryMode, DeliveryStatus, MemberRole
from mailman.interfaces.nntp import NewsgroupModeration
from mailman.interfaces.template import ITemplateManager
from mailman.interfaces.usermanager import IUserManager
from mailman.utilities.filesystem import makedirs
from mailman.utilities.i18n import search
from public import public
from sqlalchemy import Boolean
from zope.component import getUtility

log = logging.getLogger('mailman.error')


@public
class Import21Error(MailmanError):
    """An import from a Mailman 2.1 list failed."""


def bytes_to_str(value):
    # Convert a string to unicode when the encoding is not declared.
    if not isinstance(value, bytes):
        return value
    for encoding in ('ascii', 'utf-8'):
        try:
            return value.decode(encoding)
        except UnicodeDecodeError:
            continue
    # We did our best, use replace.
    return value.decode('ascii', 'replace')


def str_to_bytes(value):
    if value is None or isinstance(value, bytes):
        return value
    return value.encode('utf-8')


def seconds_to_delta(value):
    return datetime.timedelta(seconds=value)


def days_to_delta(value):
    return datetime.timedelta(days=value)


def list_members_to_unicode(value):
    return [bytes_to_str(item) for item in value]


def filter_action_mapping(value):
    # The filter_action enum values have changed.  In Mailman 2.1 the order
    # was 'Discard', 'Reject', 'Forward to List Owner', 'Preserve'.  In MM3
    # it's 'hold', 'reject', 'discard', 'accept', 'defer', 'forward',
    # 'preserve'.  Some of the MM3 actions don't exist in MM2.1.
    return {
        0: FilterAction.discard,
        1: FilterAction.reject,
        2: FilterAction.forward,
        3: FilterAction.preserve,
        }[value]


def member_moderation_action_mapping(value):
    # Convert the member_moderation_action option to an Action enum.
    # The values were: 0==Hold, 1==Reject, 2==Discard
    return {
        0: Action.hold,
        1: Action.reject,
        2: Action.discard,
        }[value]


def nonmember_action_mapping(value):
    # For default_nonmember_action, which used to be called
    # generic_nonmember_action, the values were: 0==Accept, 1==Hold,
    # 2==Reject, 3==Discard
    return {
        0: Action.accept,
        1: Action.hold,
        2: Action.reject,
        3: Action.discard,
        }[value]


def action_to_chain(value):
    # Converts an action number in Mailman 2.1 to the name of the corresponding
    # chain in 3.x.  The actions 'approve', 'subscribe' and 'unsubscribe' are
    # ignored.  The defer action is converted to None, because it is not
    # a jump to a terminal chain.
    return {
        0: None,
        # 1: 'approve',
        2: 'reject',
        3: 'discard',
        # 4: 'subscribe',
        # 5: 'unsubscribe',
        6: 'accept',
        7: 'hold',
        }[value]


def check_language_code(code):
    if code is None:
        return None
    code = bytes_to_str(code)
    if code not in getUtility(ILanguageManager):
        msg = """Missing language: {0}
You must add a section describing this language to your mailman.cfg file.
This section should look like this:
[language.{0}]
# The English name for this language.
description: CHANGE ME
# The default character set for this language.
charset: utf-8
# Whether the language is enabled or not.
enabled: yes
""".format(code)
        raise Import21Error(msg)
    return code


# Attributes in Mailman 2 which have a different type in Mailman 3.  Some
# types (e.g. bools) are autodetected from their SA column types.
TYPES = dict(
    autorespond_owner=ResponseAction,
    autorespond_postings=ResponseAction,
    autorespond_requests=ResponseAction,
    autoresponse_grace_period=days_to_delta,
    bounce_info_stale_after=seconds_to_delta,
    bounce_you_are_disabled_warnings_interval=seconds_to_delta,
    default_nonmember_action=nonmember_action_mapping,
    digest_volume_frequency=DigestFrequency,
    filter_action=filter_action_mapping,
    filter_extensions=list_members_to_unicode,
    filter_types=list_members_to_unicode,
    forward_unrecognized_bounces_to=UnrecognizedBounceDisposition,
    moderator_password=str_to_bytes,
    newsgroup_moderation=NewsgroupModeration,
    pass_extensions=list_members_to_unicode,
    pass_types=list_members_to_unicode,
    personalize=Personalization,
    preferred_language=check_language_code,
    reply_goes_to_list=ReplyToMunging,
    subscription_policy=SubscriptionPolicy,
    )


# Attribute names in Mailman 2 which are renamed in Mailman 3.
NAME_MAPPINGS = dict(
    autorespond_admin='autorespond_owner',
    autoresponse_admin_text='autoresponse_owner_text',
    autoresponse_graceperiod='autoresponse_grace_period',
    bounce_processing='process_bounces',
    bounce_unrecognized_goes_to_list_owner='forward_unrecognized_bounces_to',
    filter_filename_extensions='filter_extensions',
    filter_mime_types='filter_types',
    generic_nonmember_action='default_nonmember_action',
    include_list_post_header='allow_list_posts',
    mod_password='moderator_password',
    news_moderation='newsgroup_moderation',
    news_prefix_subject_too='nntp_prefix_subject_too',
    pass_filename_extensions='pass_extensions',
    pass_mime_types='pass_types',
    real_name='display_name',
    send_goodbye_msg='send_goodbye_message',
    send_welcome_msg='send_welcome_message',
    subscribe_policy='subscription_policy',
    )

# These DateTime fields of the mailinglist table need a type conversion to
# Python datetime object for SQLite databases.
DATETIME_COLUMNS = [
    'created_at',
    'digest_last_sent_at',
    'last_post_time',
    ]

EXCLUDES = set((
    'delivery_status',
    'digest_members',
    'members',
    'user_options',
    ))


@public
def import_config_pck(mlist, config_dict):
    """Apply a config.pck configuration dictionary to a mailing list.

    :param mlist: The mailing list.
    :type mlist: IMailingList
    :param config_dict: The Mailman 2.1 configuration dictionary.
    :type config_dict: dict
    """
    for key, value in config_dict.items():
        # Some attributes must not be directly imported.
        if key in EXCLUDES:
            continue
        # These objects need explicit type conversions.
        if key in DATETIME_COLUMNS:
            continue
        # Some attributes from Mailman 2 were renamed in Mailman 3.
        key = NAME_MAPPINGS.get(key, key)
        # Handle the simple case where the key is an attribute of the
        # IMailingList and the types are the same (modulo 8-bit/unicode
        # strings).
        #
        # If the mailing list has a preferred language that isn't registered
        # in the configuration file, hasattr() will swallow the KeyError this
        # raises and return False.  Treat that attribute specially.
        if key == 'preferred_language' or hasattr(mlist, key):
            if isinstance(value, bytes):
                value = bytes_to_str(value)
            # Some types require conversion.
            converter = TYPES.get(key)
            if converter is None:
                column = getattr(mlist.__class__, key, None)
                if column is not None and isinstance(column.type, Boolean):
                    converter = bool
            try:
                if converter is not None:
                    value = converter(value)
                setattr(mlist, key, value)
            except (TypeError, KeyError):
                print('Type conversion error for key "{}": {}'.format(
                    key, value), file=sys.stderr)
    for key in DATETIME_COLUMNS:
        try:
            value = datetime.datetime.utcfromtimestamp(config_dict[key])
        except KeyError:
            continue
        if key == 'last_post_time':
            setattr(mlist, 'last_post_at', value)
            continue
        setattr(mlist, key, value)
    # Handle the moderation policy.
    #
    # The mlist.default_member_action and mlist.default_nonmember_action enum
    # values are different in Mailman 2.1, because they have been merged into a
    # single enum in Mailman 3.
    #
    # Unmoderated lists used to have default_member_moderation set to a false
    # value; this translates to the Defer default action.  Moderated lists with
    # the default_member_moderation set to a true value used to store the
    # action in the member_moderation_action flag, the values were: 0==Hold,
    # 1=Reject, 2==Discard
    if bool(config_dict.get('default_member_moderation', 0)):
        mlist.default_member_action = member_moderation_action_mapping(
            config_dict.get('member_moderation_action'))
    else:
        mlist.default_member_action = Action.defer
    # Handle the archiving policy.  In MM2.1 there were two boolean options
    # but only three of the four possible states were valid.  Now there's just
    # an enum.
    if config_dict.get('archive'):
        # For maximum safety, if for some strange reason there's no
        # archive_private key, treat the list as having private archives.
        if config_dict.get('archive_private', True):
            mlist.archive_policy = ArchivePolicy.private
        else:
            mlist.archive_policy = ArchivePolicy.public
    else:
        mlist.archive_policy = ArchivePolicy.never
    # Handle ban list.
    ban_manager = IBanManager(mlist)
    for address in config_dict.get('ban_list', []):
        ban_manager.ban(bytes_to_str(address))
    # Handle acceptable aliases.
    acceptable_aliases = config_dict.get('acceptable_aliases', '')
    if isinstance(acceptable_aliases, bytes):
        acceptable_aliases = acceptable_aliases.decode('utf-8')
    if isinstance(acceptable_aliases, str):
        acceptable_aliases = acceptable_aliases.splitlines()
    alias_set = IAcceptableAliasSet(mlist)
    for address in acceptable_aliases:
        address = address.strip()
        if len(address) == 0:
            continue
        address = bytes_to_str(address)
        try:
            alias_set.add(address)
        except ValueError:
            # When .add() rejects this, the line probably contains a regular
            # expression.  Make that explicit for MM3.
            alias_set.add('^' + address)
    # Handle header_filter_rules conversion to header_matches.
    header_matches = IHeaderMatchList(mlist)
    header_filter_rules = config_dict.get('header_filter_rules', [])
    for line_patterns, action, _unused in header_filter_rules:
        try:
            chain = action_to_chain(action)
        except KeyError:
            log.warning('Unsupported header_filter_rules action: %r',
                        action)
            continue
        # Now split the line into a header and a pattern.
        for line_pattern in line_patterns.splitlines():
            if len(line_pattern.strip()) == 0:
                continue
            for sep in (': ', ':.*', ':.', ':'):
                header, sep, pattern = line_pattern.partition(sep)
                if sep:
                    # We found it.
                    break
            else:
                # Matches any header, which is not supported.  XXX
                log.warning('Unsupported header_filter_rules pattern: %r',
                            line_pattern)
                continue
            header = header.strip().lstrip('^').lower()
            header = header.replace('\\', '')
            if not header:
                log.warning(
                    'Cannot parse the header in header_filter_rule: %r',
                    line_pattern)
                continue
            if len(pattern) == 0:
                # The line matched only the header, therefore the header can
                # be anything.
                pattern = '.*'
            try:
                re.compile(pattern)
            except re.error:
                log.warning('Skipping header_filter rule because of an '
                            'invalid regular expression: %r', line_pattern)
                continue
            try:
                header_matches.append(header, pattern, chain)
            except ValueError:
                log.warning('Skipping duplicate header_filter rule: %r',
                            line_pattern)
                continue
    # Handle conversion to URIs.  In MM2.1, the decorations are strings
    # containing placeholders, and there's no provision for language-specific
    # templates.  In MM3, template locations are specified by URLs with the
    # special `mailman:` scheme indicating a file system path.  What we do
    # here is look to see if the list's decoration is different than the
    # default, and if so, we'll write the new decoration template to a
    # `mailman:` scheme path, then add the template to the template manager.
    convert_to_uri = {
        'welcome_msg': 'list:user:notice:welcome',
        'goodbye_msg': 'list:user:notice:goodbye',
        'msg_header': 'list:member:regular:header',
        'msg_footer': 'list:member:regular:footer',
        'digest_header': 'list:member:digest:header',
        'digest_footer': 'list:member:digest:footer',
        }
    # The best we can do is convert only the most common ones.  These are
    # order dependent; the longer substitution with the common prefix must
    # show up earlier.
    convert_placeholders = [
        ('%(real_name)s@%(host_name)s',
         'To unsubscribe send an email to ${short_listname}-leave@${domain}'),
        ('%(real_name)s mailing list',
         '$display_name mailing list -- $listname'),
        # The generic footers no longer have URLs in them.
        ('%(web_page_url)slistinfo%(cgiext)s/%(_internal_name)s\n', ''),
        ]
    # Collect defaults.
    manager = getUtility(ITemplateManager)
    defaults = {}
    for oldvar, newvar in convert_to_uri.items():
        if oldvar not in config_dict:
            continue
        text = config_dict[oldvar]
        if isinstance(text, bytes):
            text = text.decode('utf-8', 'replace')
        for oldph, newph in convert_placeholders:
            text = text.replace(oldph, newph)
        default_value, default_text = defaults.get(newvar, (None, None))
        if not text and not (default_value or default_text):
            # Both are empty, leave it.
            continue
        # Check if the value changed from the default
        try:
            expanded_text = decorate_template(mlist, text)
        except KeyError:
            # Use case: importing the old a@ex.com into b@ex.com
            # We can't check if it changed from the default
            # -> don't import, we may do more harm than good and it's easy to
            # change if needed
            # TESTME
            print('Unable to convert mailing list attribute:', oldvar,
                  'with value "{}"'.format(text),
                  file=sys.stderr)
            continue
        if (expanded_text and default_text and
                expanded_text.strip() == default_text.strip()):
            # Keep the default.
            continue
        # Write the custom value to the right file and add it to the template
        # manager for real.
        base_uri = 'mailman:///$listname/$language/'
        if default_value:
            filename = default_value.rpartition('/')[2]
        else:
            filename = '{}.txt'.format(newvar.replace(':', '_'))
        if not default_value or not default_value.startswith(base_uri):
            manager.set(newvar, mlist.list_id, base_uri + filename)
        filepath = list(search(filename, mlist))[0]
        makedirs(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as fp:
            fp.write(text)
    # Import rosters.
    regulars_set = set(config_dict.get('members', {}))
    digesters_set = set(config_dict.get('digest_members', {}))
    members = regulars_set.union(digesters_set)
    # Don't send welcome messages when we import the rosters.
    send_welcome_message = mlist.send_welcome_message
    mlist.send_welcome_message = False
    try:
        import_roster(mlist, config_dict, members, MemberRole.member)
        import_roster(mlist, config_dict, config_dict.get('owner', []),
                      MemberRole.owner)
        import_roster(mlist, config_dict, config_dict.get('moderator', []),
                      MemberRole.moderator)
        # Now import the '*_these_nonmembers' properties, filtering out the
        # regexps which will remain in the property.
        for action_name in ('accept', 'hold', 'reject', 'discard'):
            prop_name = '{}_these_nonmembers'.format(action_name)
            emails = [addr
                      for addr in config_dict.get(prop_name, [])
                      if not addr.startswith('^')]
            import_roster(mlist, config_dict, emails, MemberRole.nonmember,
                          Action[action_name])
            # Only keep the regexes in the legacy list property.
            list_prop = getattr(mlist, prop_name)
            for email in emails:
                list_prop.remove(email)
    finally:
        mlist.send_welcome_message = send_welcome_message


def import_roster(mlist, config_dict, members, role, action=None):
    """Import members lists from a config.pck configuration dictionary.

    :param mlist: The mailing list.
    :type mlist: IMailingList
    :param config_dict: The Mailman 2.1 configuration dictionary.
    :type config_dict: dict
    :param members: The members list to import.
    :type members: list
    :param role: The MemberRole to import them as.
    :type role: MemberRole enum
    :param action: The default nonmember action.
    :type action: Action
    """
    usermanager = getUtility(IUserManager)
    validator = getUtility(IEmailValidator)
    roster = mlist.get_roster(role)
    for email in members:
        # For owners and members, the emails can have a mixed case, so
        # lowercase them all.
        email = bytes_to_str(email).lower()
        if roster.get_member(email) is not None:
            print('{} is already imported with role {}'.format(email, role),
                  file=sys.stderr)
            continue
        address = usermanager.get_address(email)
        user = usermanager.get_user(email)
        if user is None:
            user = usermanager.create_user()
            if address is None:
                merged_members = {}
                merged_members.update(config_dict.get('members', {}))
                merged_members.update(config_dict.get('digest_members', {}))
                if merged_members.get(email, 0) != 0:
                    original_email = bytes_to_str(merged_members[email])
                    if not validator.is_valid(original_email):
                        original_email = email
                else:
                    original_email = email
                if not validator.is_valid(original_email):
                    # Skip this one entirely.
                    continue
                address = usermanager.create_address(original_email)
                address.verified_on = datetime.datetime.now()
            user.link(address)
        member = mlist.subscribe(address, role)
        assert member is not None
        prefs = config_dict.get('user_options', {}).get(email)
        if email in config_dict.get('members', {}):
            member.preferences.delivery_mode = DeliveryMode.regular
        elif email in config_dict.get('digest_members', {}):
            if prefs is not None and prefs & 8:               # DisableMime
                member.preferences.delivery_mode = \
                  DeliveryMode.plaintext_digests
            else:
                member.preferences.delivery_mode = DeliveryMode.mime_digests
        else:
            # XXX Probably not adding a member role here.
            pass
        if email in config_dict.get('language', {}):
            member.preferences.preferred_language = \
                check_language_code(config_dict['language'][email])
        # If the user already exists, display_name and password will be
        # overwritten.
        if email in config_dict.get('usernames', {}):
            address.display_name = \
                bytes_to_str(config_dict['usernames'][email])
            user.display_name = \
                bytes_to_str(config_dict['usernames'][email])
        if email in config_dict.get('passwords', {}):
            user.password = config.password_context.encrypt(
                config_dict['passwords'][email])
        # delivery_status
        oldds = config_dict.get('delivery_status', {}).get(email, (0, 0))[0]
        if oldds == 0:
            member.preferences.delivery_status = DeliveryStatus.enabled
        elif oldds == 1:
            member.preferences.delivery_status = DeliveryStatus.unknown
        elif oldds == 2:
            member.preferences.delivery_status = DeliveryStatus.by_user
        elif oldds == 3:
            member.preferences.delivery_status = DeliveryStatus.by_moderator
        elif oldds == 4:
            member.preferences.delivery_status = DeliveryStatus.by_bounces
        # Moderation.
        if prefs is not None:
            # We're adding a member.
            if prefs & 128:
                # The member is moderated.  Check the member_moderation_action
                # option to know which action should be taken.
                action = member_moderation_action_mapping(
                    config_dict.get('member_moderation_action'))
            else:
                # Member is not moderated: defer is the best option, as
                # discussed on merge request 100.
                action = Action.defer
        if action is not None:
            # Either this was set right above or in the function's arguments
            # for nonmembers.
            member.moderation_action = action
        # Other preferences.
        if prefs is not None:
            # AcknowledgePosts
            member.preferences.acknowledge_posts = bool(prefs & 4)
            # ConcealSubscription
            member.preferences.hide_address = bool(prefs & 16)
            # DontReceiveOwnPosts
            member.preferences.receive_own_postings = not bool(prefs & 2)
            # DontReceiveDuplicates
            member.preferences.receive_list_copy = not bool(prefs & 256)
