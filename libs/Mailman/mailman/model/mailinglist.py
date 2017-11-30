# Copyright (C) 2006-2017 by the Free Software Foundation, Inc.
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

"""Model for mailing lists."""

import os

from mailman.config import config
from mailman.database.model import Model
from mailman.database.transaction import dbconnection
from mailman.database.types import Enum, SAUnicode, SAUnicodeLarge
from mailman.interfaces.action import Action, FilterAction
from mailman.interfaces.address import IAddress
from mailman.interfaces.archiver import ArchivePolicy
from mailman.interfaces.autorespond import ResponseAction
from mailman.interfaces.bounce import UnrecognizedBounceDisposition
from mailman.interfaces.digests import DigestFrequency
from mailman.interfaces.domain import IDomainManager
from mailman.interfaces.languages import ILanguageManager
from mailman.interfaces.mailinglist import (
    DMARCMitigateAction, IAcceptableAlias, IAcceptableAliasSet,
    IHeaderMatch, IHeaderMatchList, IListArchiver, IListArchiverSet,
    IMailingList, Personalization, ReplyToMunging, SubscriptionPolicy)
from mailman.interfaces.member import (
    AlreadySubscribedError, MemberRole, MissingPreferredAddressError,
    SubscriptionEvent)
from mailman.interfaces.mime import FilterType
from mailman.interfaces.nntp import NewsgroupModeration
from mailman.interfaces.user import IUser
from mailman.model import roster
from mailman.model.digests import OneLastDigest
from mailman.model.member import Member
from mailman.model.mime import ContentFilter
from mailman.model.preferences import Preferences
from mailman.utilities.filesystem import makedirs
from mailman.utilities.string import expand
from public import public
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, Interval,
    LargeBinary, PickleType)
from sqlalchemy.event import listen
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound
from zope.component import getUtility
from zope.event import notify
from zope.interface import implementer


SPACE = ' '
UNDERSCORE = '_'


@public
@implementer(IMailingList)
class MailingList(Model):
    """See `IMailingList`."""

    __tablename__ = 'mailinglist'

    id = Column(Integer, primary_key=True)

    # XXX denotes attributes that should be part of the public interface but
    # are currently missing.

    # List identity
    list_name = Column(SAUnicode, index=True)
    mail_host = Column(SAUnicode, index=True)
    _list_id = Column('list_id', SAUnicode, index=True, unique=True)
    allow_list_posts = Column(Boolean)
    include_rfc2369_headers = Column(Boolean)
    advertised = Column(Boolean)
    anonymous_list = Column(Boolean)
    # Attributes not directly modifiable via the web u/i
    created_at = Column(DateTime)
    # Attributes which are directly modifiable via the web u/i.  The more
    # complicated attributes are currently stored as pickles, though that
    # will change as the schema and implementation is developed.
    next_request_id = Column(Integer)
    next_digest_number = Column(Integer)
    digest_last_sent_at = Column(DateTime)
    volume = Column(Integer)
    last_post_at = Column(DateTime)
    # Attributes which are directly modifiable via the web u/i.  The more
    # complicated attributes are currently stored as pickles, though that
    # will change as the schema and implementation is developed.
    accept_these_nonmembers = Column(PickleType)       # XXX
    admin_immed_notify = Column(Boolean)
    admin_notify_mchanges = Column(Boolean)
    administrivia = Column(Boolean)
    archive_policy = Column(Enum(ArchivePolicy))
    # Automatic responses.
    autoresponse_grace_period = Column(Interval)
    autorespond_owner = Column(Enum(ResponseAction))
    autoresponse_owner_text = Column(SAUnicode)
    autorespond_postings = Column(Enum(ResponseAction))
    autoresponse_postings_text = Column(SAUnicode)
    autorespond_requests = Column(Enum(ResponseAction))
    autoresponse_request_text = Column(SAUnicode)
    # Content filters.
    filter_action = Column(Enum(FilterAction))
    filter_content = Column(Boolean)
    collapse_alternatives = Column(Boolean)
    convert_html_to_plaintext = Column(Boolean)
    # Bounces.
    bounce_info_stale_after = Column(Interval)                   # XXX
    bounce_matching_headers = Column(SAUnicode)                  # XXX
    bounce_notify_owner_on_disable = Column(Boolean)             # XXX
    bounce_notify_owner_on_removal = Column(Boolean)             # XXX
    bounce_score_threshold = Column(Integer)                     # XXX
    bounce_you_are_disabled_warnings = Column(Integer)           # XXX
    bounce_you_are_disabled_warnings_interval = Column(Interval)  # XXX
    forward_unrecognized_bounces_to = Column(
        Enum(UnrecognizedBounceDisposition))
    process_bounces = Column(Boolean)
    # DMARC
    dmarc_mitigate_action = Column(Enum(DMARCMitigateAction))
    dmarc_mitigate_unconditionally = Column(Boolean)
    dmarc_moderation_notice = Column(SAUnicodeLarge)
    dmarc_wrapped_message_text = Column(SAUnicodeLarge)
    # Miscellaneous
    default_member_action = Column(Enum(Action))
    default_nonmember_action = Column(Enum(Action))
    description = Column(SAUnicode)
    digests_enabled = Column(Boolean)
    digest_is_default = Column(Boolean)
    digest_send_periodic = Column(Boolean)
    digest_size_threshold = Column(Float)
    digest_volume_frequency = Column(Enum(DigestFrequency))
    discard_these_nonmembers = Column(PickleType)
    emergency = Column(Boolean)
    encode_ascii_prefixes = Column(Boolean)
    first_strip_reply_to = Column(Boolean)
    forward_auto_discards = Column(Boolean)
    gateway_to_mail = Column(Boolean)
    gateway_to_news = Column(Boolean)
    hold_these_nonmembers = Column(PickleType)
    info = Column(SAUnicode)
    linked_newsgroup = Column(SAUnicode)
    max_days_to_hold = Column(Integer)
    max_message_size = Column(Integer)
    max_num_recipients = Column(Integer)
    member_moderation_notice = Column(SAUnicode)
    mime_is_default_digest = Column(Boolean)
    # FIXME: There should be no moderator_password
    moderator_password = Column(LargeBinary)             # TODO : was RawStr()
    newsgroup_moderation = Column(Enum(NewsgroupModeration))
    nntp_prefix_subject_too = Column(Boolean)
    nonmember_rejection_notice = Column(SAUnicode)
    obscure_addresses = Column(Boolean)
    owner_chain = Column(SAUnicode)
    owner_pipeline = Column(SAUnicode)
    personalize = Column(Enum(Personalization))
    post_id = Column(Integer)
    posting_chain = Column(SAUnicode)
    posting_pipeline = Column(SAUnicode)
    _preferred_language = Column('preferred_language', SAUnicode)
    display_name = Column(SAUnicode)
    reject_these_nonmembers = Column(PickleType)
    reply_goes_to_list = Column(Enum(ReplyToMunging))
    reply_to_address = Column(SAUnicode)
    require_explicit_destination = Column(Boolean)
    respond_to_post_requests = Column(Boolean)
    scrub_nondigest = Column(Boolean)
    send_goodbye_message = Column(Boolean)
    send_welcome_message = Column(Boolean)
    subject_prefix = Column(SAUnicode)
    subscription_policy = Column(Enum(SubscriptionPolicy))
    topics = Column(PickleType)
    topics_bodylines_limit = Column(Integer)
    topics_enabled = Column(Boolean)
    unsubscription_policy = Column(Enum(SubscriptionPolicy))
    # ORM relationships.
    header_matches = relationship(
        'HeaderMatch', backref='mailing_list',
        cascade="all, delete-orphan",
        order_by="HeaderMatch._position")

    def __init__(self, fqdn_listname):
        super().__init__()
        listname, at, hostname = fqdn_listname.partition('@')
        assert hostname, 'Bad list name: {0}'.format(fqdn_listname)
        self.list_name = listname
        self.mail_host = hostname
        self._list_id = '{0}.{1}'.format(listname, hostname)
        # For the pending database
        self.next_request_id = 1
        # We need to set up the rosters.  Normally, this method will get called
        # when the MailingList object is loaded from the database, but when the
        # constructor is called, SQLAlchemy's `load` event isn't triggered.
        # Thus we need to set up the rosters explicitly.
        self._post_load()
        makedirs(self.data_path)

    def _post_load(self, *args):
        # This hooks up to SQLAlchemy's `load` event.
        self.owners = roster.OwnerRoster(self)
        self.moderators = roster.ModeratorRoster(self)
        self.administrators = roster.AdministratorRoster(self)
        self.members = roster.MemberRoster(self)
        self.regular_members = roster.RegularMemberRoster(self)
        self.digest_members = roster.DigestMemberRoster(self)
        self.subscribers = roster.Subscribers(self)
        self.nonmembers = roster.NonmemberRoster(self)

    @classmethod
    def __declare_last__(cls):
        # SQLAlchemy special directive hook called after mappings are assumed
        # to be complete.  Use this to connect the roster instance creation
        # method with the SA `load` event.
        listen(cls, 'load', cls._post_load)

    def __repr__(self):
        return '<mailing list "{0}" at {1:#x}>'.format(
            self.fqdn_listname, id(self))

    @property
    def fqdn_listname(self):
        """See `IMailingList`."""
        return '{0}@{1}'.format(self.list_name, self.mail_host)

    @property
    def list_id(self):
        """See `IMailingList`."""
        return self._list_id

    @property
    def domain(self):
        """See `IMailingList`."""
        return getUtility(IDomainManager)[self.mail_host]

    @property
    def data_path(self):
        """See `IMailingList`."""
        return os.path.join(config.LIST_DATA_DIR, self.list_id)

    # IMailingListAddresses

    @property
    def posting_address(self):
        """See `IMailingList`."""
        return self.fqdn_listname

    @property
    def no_reply_address(self):
        """See `IMailingList`."""
        return '{}@{}'.format(config.mailman.noreply_address, self.mail_host)

    @property
    def owner_address(self):
        """See `IMailingList`."""
        return '{}-owner@{}'.format(self.list_name, self.mail_host)

    @property
    def request_address(self):
        """See `IMailingList`."""
        return '{}-request@{}'.format(self.list_name, self.mail_host)

    @property
    def bounces_address(self):
        """See `IMailingList`."""
        return '{}-bounces@{}'.format(self.list_name, self.mail_host)

    @property
    def join_address(self):
        """See `IMailingList`."""
        return '{}-join@{}'.format(self.list_name, self.mail_host)

    @property
    def leave_address(self):
        """See `IMailingList`."""
        return '{}-leave@{}'.format(self.list_name, self.mail_host)

    @property
    def subscribe_address(self):
        """See `IMailingList`."""
        return '{}-subscribe@{}'.format(self.list_name, self.mail_host)

    @property
    def unsubscribe_address(self):
        """See `IMailingList`."""
        return '{}-unsubscribe@{}'.format(self.list_name, self.mail_host)

    def confirm_address(self, cookie):
        """See `IMailingList`."""
        local_part = expand(config.mta.verp_confirm_format, self, dict(
            address='{}-confirm'.format(self.list_name),
            cookie=cookie))
        return '{}@{}'.format(local_part, self.mail_host)

    @property
    def preferred_language(self):
        """See `IMailingList`."""
        return getUtility(ILanguageManager)[self._preferred_language]

    @preferred_language.setter
    def preferred_language(self, language):
        """See `IMailingList`."""
        # Accept both a language code and a `Language` instance.
        try:
            self._preferred_language = language.code
        except AttributeError:
            self._preferred_language = language

    @dbconnection
    def send_one_last_digest_to(self, store, address, delivery_mode):
        """See `IMailingList`."""
        digest = OneLastDigest(self, address, delivery_mode)
        store.add(digest)

    @property
    @dbconnection
    def last_digest_recipients(self, store):
        """See `IMailingList`."""
        results = store.query(OneLastDigest).filter(
            OneLastDigest.mailing_list == self)
        recipients = [(digest.address, digest.delivery_mode)
                      for digest in results]
        results.delete()
        return recipients

    @property
    @dbconnection
    def filter_types(self, store):
        """See `IMailingList`."""
        results = store.query(ContentFilter).filter(
            ContentFilter.mailing_list == self,
            ContentFilter.filter_type == FilterType.filter_mime)
        for content_filter in results:
            yield content_filter.filter_pattern

    @filter_types.setter
    @dbconnection
    def filter_types(self, store, sequence):
        """See `IMailingList`."""
        # First, delete all existing MIME type filter patterns.
        results = store.query(ContentFilter).filter(
            ContentFilter.mailing_list == self,
            ContentFilter.filter_type == FilterType.filter_mime)
        results.delete()
        # Now add all the new filter types.
        for mime_type in sequence:
            content_filter = ContentFilter(
                self, mime_type, FilterType.filter_mime)
            store.add(content_filter)

    @property
    @dbconnection
    def pass_types(self, store):
        """See `IMailingList`."""
        results = store.query(ContentFilter).filter(
            ContentFilter.mailing_list == self,
            ContentFilter.filter_type == FilterType.pass_mime)
        for content_filter in results:
            yield content_filter.filter_pattern

    @pass_types.setter
    @dbconnection
    def pass_types(self, store, sequence):
        """See `IMailingList`."""
        # First, delete all existing MIME type pass patterns.
        results = store.query(ContentFilter).filter(
            ContentFilter.mailing_list == self,
            ContentFilter.filter_type == FilterType.pass_mime)
        results.delete()
        # Now add all the new filter types.
        for mime_type in sequence:
            content_filter = ContentFilter(
                self, mime_type, FilterType.pass_mime)
            store.add(content_filter)

    @property
    @dbconnection
    def filter_extensions(self, store):
        """See `IMailingList`."""
        results = store.query(ContentFilter).filter(
            ContentFilter.mailing_list == self,
            ContentFilter.filter_type == FilterType.filter_extension)
        for content_filter in results:
            yield content_filter.filter_pattern

    @filter_extensions.setter
    @dbconnection
    def filter_extensions(self, store, sequence):
        """See `IMailingList`."""
        # First, delete all existing file extensions filter patterns.
        results = store.query(ContentFilter).filter(
            ContentFilter.mailing_list == self,
            ContentFilter.filter_type == FilterType.filter_extension)
        results.delete()
        # Now add all the new filter types.
        for mime_type in sequence:
            content_filter = ContentFilter(
                self, mime_type, FilterType.filter_extension)
            store.add(content_filter)

    @property
    @dbconnection
    def pass_extensions(self, store):
        """See `IMailingList`."""
        results = store.query(ContentFilter).filter(
            ContentFilter.mailing_list == self,
            ContentFilter.filter_type == FilterType.pass_extension)
        for content_filter in results:
            yield content_filter.filter_pattern

    @pass_extensions.setter
    @dbconnection
    def pass_extensions(self, store, sequence):
        """See `IMailingList`."""
        # First, delete all existing file extensions pass patterns.
        results = store.query(ContentFilter).filter(
            ContentFilter.mailing_list == self,
            ContentFilter.filter_type == FilterType.pass_extension)
        results.delete()
        # Now add all the new filter types.
        for mime_type in sequence:
            content_filter = ContentFilter(
                self, mime_type, FilterType.pass_extension)
            store.add(content_filter)

    def get_roster(self, role):
        """See `IMailingList`."""
        if role is MemberRole.member:
            return self.members
        elif role is MemberRole.owner:
            return self.owners
        elif role is MemberRole.moderator:
            return self.moderators
        elif role is MemberRole.nonmember:
            return self.nonmembers
        else:
            raise ValueError('Undefined MemberRole: {}'.format(role))

    def _get_subscriber(self, store, subscriber, role):
        """Get some information about a user/address.

        Returns a 2-tuple of (member, email) for the given subscriber.  If the
        subscriber is is not an ``IAddress`` or ``IUser``, then a 2-tuple of
        (None, None) is returned.  If the subscriber is not already
        subscribed, then (None, email) is returned.  If the subscriber is an
        ``IUser`` and does not have a preferred address, (member, None) is
        returned.
        """
        member = None
        email = None
        if IAddress.providedBy(subscriber):
            member = store.query(Member).filter(
                Member.role == role,
                Member.list_id == self._list_id,
                Member._address == subscriber).first()
            email = subscriber.email
        elif IUser.providedBy(subscriber):
            if subscriber.preferred_address is None:
                raise MissingPreferredAddressError(subscriber)
            email = subscriber.preferred_address.email
            member = store.query(Member).filter(
                Member.role == role,
                Member.list_id == self._list_id,
                Member._user == subscriber).first()
        return member, email

    @dbconnection
    def is_subscribed(self, store, subscriber, role=MemberRole.member):
        """See `IMailingList`."""
        member, email = self._get_subscriber(store, subscriber, role)
        return member is not None

    @dbconnection
    def subscribe(self, store, subscriber, role=MemberRole.member):
        """See `IMailingList`."""
        member, email = self._get_subscriber(store, subscriber, role)
        if member is not None:
            raise AlreadySubscribedError(self.fqdn_listname, email, role)
        member = Member(role=role,
                        list_id=self._list_id,
                        subscriber=subscriber)
        member.preferences = Preferences()
        store.add(member)
        notify(SubscriptionEvent(self, member))
        return member


@public
@implementer(IAcceptableAlias)
class AcceptableAlias(Model):
    """See `IAcceptableAlias`."""

    __tablename__ = 'acceptablealias'

    id = Column(Integer, primary_key=True)

    mailing_list_id = Column(
        Integer, ForeignKey('mailinglist.id'),
        index=True, nullable=False)
    mailing_list = relationship('MailingList', backref='acceptablealias')
    alias = Column(SAUnicode, index=True, nullable=False)

    def __init__(self, mailing_list, alias):
        super().__init__()
        self.mailing_list = mailing_list
        self.alias = alias


@public
@implementer(IAcceptableAliasSet)
class AcceptableAliasSet:
    """See `IAcceptableAliasSet`."""

    def __init__(self, mailing_list):
        self._mailing_list = mailing_list

    @dbconnection
    def clear(self, store):
        """See `IAcceptableAliasSet`."""
        store.query(AcceptableAlias).filter(
            AcceptableAlias.mailing_list == self._mailing_list).delete()

    @dbconnection
    def add(self, store, alias):
        if not (alias.startswith('^') or '@' in alias):
            raise ValueError(alias)
        alias = AcceptableAlias(self._mailing_list, alias.lower())
        store.add(alias)

    @dbconnection
    def remove(self, store, alias):
        store.query(AcceptableAlias).filter(
            AcceptableAlias.mailing_list == self._mailing_list,
            AcceptableAlias.alias == alias.lower()).delete()

    @property
    @dbconnection
    def aliases(self, store):
        aliases = store.query(AcceptableAlias).filter(
            AcceptableAlias.mailing_list_id == self._mailing_list.id)
        for alias in aliases:
            yield alias.alias


@public
@implementer(IListArchiver)
class ListArchiver(Model):
    """See `IListArchiver`."""

    __tablename__ = 'listarchiver'

    id = Column(Integer, primary_key=True)

    mailing_list_id = Column(
        Integer, ForeignKey('mailinglist.id'),
        index=True, nullable=False)
    mailing_list = relationship('MailingList')

    name = Column(SAUnicode, nullable=False)
    _is_enabled = Column(Boolean)

    def __init__(self, mailing_list, archiver_name, system_archiver):
        self.mailing_list = mailing_list
        self.name = archiver_name
        self._is_enabled = system_archiver.is_enabled

    @property
    def system_archiver(self):
        for archiver in config.archivers:           # pragma: no branch
            if archiver.name == self.name:
                return archiver
        raise AssertionError('Archiver not found: {}'.format(self.name))

    @property
    def is_enabled(self):
        return self.system_archiver.is_enabled and self._is_enabled

    @is_enabled.setter
    def is_enabled(self, value):
        self._is_enabled = value


@public
@implementer(IListArchiverSet)
class ListArchiverSet:
    @dbconnection
    def __init__(self, store, mailing_list):
        self._mailing_list = mailing_list
        system_archivers = {}
        for archiver in config.archivers:
            system_archivers[archiver.name] = archiver
        # Add any system enabled archivers which aren't already associated
        # with the mailing list.
        for archiver_name in system_archivers:
            exists = store.query(ListArchiver).filter(
                ListArchiver.mailing_list == mailing_list,
                ListArchiver.name == archiver_name).one_or_none()
            if exists is None:
                store.add(ListArchiver(mailing_list, archiver_name,
                                       system_archivers[archiver_name]))

    @property
    @dbconnection
    def archivers(self, store):
        entries = store.query(ListArchiver).filter(
            ListArchiver.mailing_list == self._mailing_list)
        yield from entries

    @dbconnection
    def get(self, store, archiver_name):
        return store.query(ListArchiver).filter(
            ListArchiver.mailing_list == self._mailing_list,
            ListArchiver.name == archiver_name).one_or_none()


@public
@implementer(IHeaderMatch)
class HeaderMatch(Model):
    """See `IHeaderMatch`."""

    __tablename__ = 'headermatch'

    id = Column(Integer, primary_key=True)

    mailing_list_id = Column(
        Integer,
        ForeignKey('mailinglist.id'),
        index=True, nullable=False)

    _position = Column('position', Integer, index=True, default=0)
    header = Column(SAUnicode)
    pattern = Column(SAUnicode)
    chain = Column(SAUnicode, nullable=True)

    def __init__(self, **kw):
        position = kw.pop('position', None)
        if position is not None:
            kw['_position'] = position
        super().__init__(**kw)

    @hybrid_property
    def position(self):
        """See `IHeaderMatch`."""
        return self._position

    @position.setter
    @dbconnection
    def position(self, store, value):
        """See `IHeaderMatch`."""
        if value < 0:
            raise ValueError('Negative indexes are not supported')
        if value == self.position:
            # Nothing to do.
            return
        existing_count = store.query(HeaderMatch).filter(
            HeaderMatch.mailing_list == self.mailing_list).count()
        if value >= existing_count:
            raise ValueError(
                'There are {count} header matches for this list, '
                'the new position cannot be {count} or higher'.format(
                    count=existing_count))
        if value < self.position:
            # Moving up: header matches between the new position and the
            # current one must be moved down the list to make room. Those
            # after the current position must not be changed.
            for header_match in store.query(HeaderMatch).filter(
                    HeaderMatch.mailing_list == self.mailing_list,
                    HeaderMatch.position >= value,
                    HeaderMatch.position < self.position):
                header_match._position = header_match.position + 1
        elif value > self.position:
            # Moving down: header matches between the current position and the
            # new one must be moved up the list to make room. Those after the
            # new position must not be changed.
            for header_match in store.query(HeaderMatch).filter(
                    HeaderMatch.mailing_list == self.mailing_list,
                    HeaderMatch.position > self.position,
                    HeaderMatch.position <= value):
                header_match._position = header_match.position - 1
        self._position = value


@public
@implementer(IHeaderMatchList)
class HeaderMatchList:
    """See `IHeaderMatchList`."""

    # All write operations must mark the mailing list's header_matches
    # collection as expired:
    # http://docs.sqlalchemy.org/en/latest/orm/session_state_management.html#refreshing-expiring

    def __init__(self, mailing_list):
        self._mailing_list = mailing_list

    @dbconnection
    def clear(self, store):
        """See `IHeaderMatchList`."""
        # http://docs.sqlalchemy.org/en/latest/orm/session_basics.html#deleting-from-collections
        del self._mailing_list.header_matches[:]

    @dbconnection
    def append(self, store, header, pattern, chain=None):
        header = header.lower()
        existing = store.query(HeaderMatch).filter(
            HeaderMatch.mailing_list == self._mailing_list,
            HeaderMatch.header == header,
            HeaderMatch.pattern == pattern).count()
        if existing > 0:
            raise ValueError('Pattern already exists')
        last_position = store.query(HeaderMatch.position).filter(
            HeaderMatch.mailing_list == self._mailing_list
            ).order_by(HeaderMatch.position.desc()).limit(1).scalar()
        if last_position is None:
            last_position = -1
        header_match = HeaderMatch(
            mailing_list=self._mailing_list,
            header=header, pattern=pattern, chain=chain,
            position=last_position + 1)
        store.add(header_match)
        store.expire(self._mailing_list, ['header_matches'])

    @dbconnection
    def insert(self, store, index, header, pattern, chain=None):
        self.append(header, pattern, chain)
        # Get the header match that was just added.
        header_match = store.query(HeaderMatch).filter(
            HeaderMatch.mailing_list == self._mailing_list,
            HeaderMatch.header == header.lower(),
            HeaderMatch.pattern == pattern,
            HeaderMatch.chain == chain).one()
        header_match.position = index
        store.expire(self._mailing_list, ['header_matches'])

    @dbconnection
    def remove(self, store, header, pattern):
        header = header.lower()
        # Query.delete() has many caveats, don't use it here:
        # http://docs.sqlalchemy.org/en/rel_1_0/orm/query.html#sqlalchemy.orm.query.Query.delete
        try:
            existing = store.query(HeaderMatch).filter(
                HeaderMatch.mailing_list == self._mailing_list,
                HeaderMatch.header == header,
                HeaderMatch.pattern == pattern).one()
        except NoResultFound:
            raise ValueError('Pattern does not exist')
        else:
            store.delete(existing)
        self._restore_position_sequence()
        store.expire(self._mailing_list, ['header_matches'])

    @dbconnection
    def __getitem__(self, store, index):
        if index < 0:
            index = len(self) + index
        try:
            return store.query(HeaderMatch).filter(
                HeaderMatch.mailing_list == self._mailing_list,
                HeaderMatch.position == index).one()
        except NoResultFound:
            raise IndexError

    @dbconnection
    def __delitem__(self, store, index):
        try:
            existing = store.query(HeaderMatch).filter(
                HeaderMatch.mailing_list == self._mailing_list,
                HeaderMatch.position == index).one()
        except NoResultFound:
            raise IndexError
        else:
            store.delete(existing)
        self._restore_position_sequence()
        store.expire(self._mailing_list, ['header_matches'])

    @dbconnection
    def __len__(self, store):
        return store.query(HeaderMatch).filter(
            HeaderMatch.mailing_list == self._mailing_list).count()

    @dbconnection
    def __iter__(self, store):
        yield from store.query(HeaderMatch).filter(
            HeaderMatch.mailing_list == self._mailing_list
            ).order_by(HeaderMatch.position)

    @dbconnection
    def _restore_position_sequence(self, store):
        # Restore a continuous position sequence for this mailing list's
        # header matches.
        #
        # The header match positions may not be continuous after deleting an
        # item.  It won't prevent this component from working properly, but
        # it's cleaner to restore a continuous sequence.
        for position, match in enumerate(store.query(HeaderMatch).filter(
                HeaderMatch.mailing_list == self._mailing_list
                ).order_by(HeaderMatch.position)):
            match._position = position
        store.expire(self._mailing_list, ['header_matches'])
