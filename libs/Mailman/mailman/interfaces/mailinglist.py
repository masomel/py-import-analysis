# Copyright (C) 2007-2017 by the Free Software Foundation, Inc.
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

"""Interface for a mailing list."""

from enum import Enum
from mailman.interfaces.address import InvalidEmailAddressError
from mailman.interfaces.member import MemberRole
from public import public
from zope.interface import Attribute, Interface


@public
class InvalidListNameError(InvalidEmailAddressError):
    """List name is invalid."""

    def __init__(self, listname):
        super().__init__('{}@'.format(listname))
        self.listname = listname


@public
class DMARCMitigateAction(Enum):
    # Mitigations to apply to messages From: domains publishing an applicable
    # DMARC policy, or unconditionally depending on settings.
    #
    # No DMARC mitigations.
    no_mitigation = 0
    # Messages From: domains with DMARC policy will have From: replaced by the
    # list posting address and the original From: added to Reply-To: or Cc:.
    munge_from = 1
    # Messages From: domains with DMARC policy will be wrapped in an outer
    # message From: the list posting address.
    wrap_message = 2
    # Messages From: domains with DMARC policy will be rejected.
    reject = 3
    # Messages From: domains with DMARC policy will be discarded.
    discard = 4


@public
class Personalization(Enum):
    none = 0
    # Everyone gets a unique copy of the message, and there are a few more
    # substitution variables, but no headers are modified.
    individual = 1
    # All of the 'individual' personalization plus recipient header
    # modification.
    full = 2


@public
class ReplyToMunging(Enum):
    # The Reply-To header is passed through untouched
    no_munging = 0
    # The mailing list's posting address is appended to the Reply-To header
    point_to_list = 1
    # An explicit Reply-To header is added
    explicit_header = 2


@public
class SubscriptionPolicy(Enum):
    """All subscription/unsubscription policies for a mailing list."""
    # Neither confirmation, nor moderator approval is required.
    open = 0
    # The user must confirm the subscription.
    confirm = 1
    # The moderator must approve the subscription.
    moderate = 2
    # The user must first confirm their subscription, and then if that is
    # successful, the moderator must also approve it.
    confirm_then_moderate = 3


@public
class IMailingList(Interface):
    """A mailing list."""

    # List identity

    created_at = Attribute(
        """The date and time that the mailing list was created.""")

    list_name = Attribute("""\
        The read-only short name of the mailing list.  Note that where a
        Mailman installation supports multiple domains, this short name may
        not be unique.  Use the fqdn_listname attribute for a guaranteed
        unique id for the mailing list.  This short name is always the local
        part of the posting email address.  For example, if messages are
        posted to mylist@example.com, then the list_name is 'mylist'.
        """)

    mail_host = Attribute("""\
        The read-only domain name 'hosting' this mailing list.  This is always
        the domain name part of the posting email address, and it may bear no
        relationship to the web url used to access this mailing list.  For
        example, if messages are posted to mylist@example.com, then the
        mail_host is 'example.com'.
        """)

    list_id = Attribute("""\
        The identity of the mailing list.  This value will never change.  It
        is defined in RFC 2369.
        """)

    fqdn_listname = Attribute("""\
        The read-only fully qualified name of the mailing list.  This is the
        guaranteed unique id for the mailing list, and it is always the
        address to which messages are posted, e.g. mylist@example.com.  It is
        always comprised of the list_name + '@' + mail_host.
        """)

    domain = Attribute(
        """The `IDomain` that this mailing list is defined in.""")

    display_name = Attribute("""\
        The short human-readable descriptive name for the mailing list.  This
        is used in locations such as the message footers and as the default
        value for the Subject prefix.
        """)

    description = Attribute("""\
        A terse phrase identifying this mailing list.

        This description is used when the mailing list is listed with other
        mailing lists, or in headers, and so forth.  It should be as succinct
        as you can get it, while still identifying what the list is.""")

    info = Attribute("""\
        A longer description of this mailing list.  This can be any arbitrary
        text, up to a database-specific maximum length.
        """)

    preferred_language = Attribute("""\
        The default language for communications on this mailing list.

        When the list sends out notifications, it will be in this language,
        unless the recipient is a known user and that user has a preferred
        language.
        """)

    subject_prefix = Attribute("""\
        The text to insert at the front of the Subject field.

        When messages posted to this mailing list are sent to the list
        subscribers, the Subject header may be rewritten to include an
        identifying prefix.  Typically this prefix will appear in square
        brackets and the default value inside the brackets is taken as the
        list's display name.  However, any value can be used, including the
        empty string to prevent Subject header rewriting.
        """)

    allow_list_posts = Attribute(
        """Flag specifying posts to the list are generally allowed.

        This controls the value of the RFC 2369 List-Post header.  This is
        usually set to True, except for announce-only lists.  When False, the
        List-Post is set to NO as per the RFC.
        """)

    include_rfc2369_headers = Attribute(
        """Flag specifying whether to include any RFC 2369 header, including
        the RFC 2919 List-ID header.""")

    anonymous_list = Attribute(
        """Flag controlling whether messages to this list are anonymized.

        Anonymizing messages is not perfect, however setting this flag removes
        the sender of the message (in the From, Sender, and Reply-To fields)
        and replaces these with the list's posting address.
        """)

    advertised = Attribute(
        """Advertise this mailing list when people ask for an overview of the
        available mailing lists.""")

    # Contact addresses

    posting_address = Attribute(
        """The address to which messages are posted for copying to the full
        list membership, where 'full' of course means those members for which
        delivery is currently enabled.
        """)

    no_reply_address = Attribute(
        """The address to which all messages will be immediately discarded,
        without prejudice or record.  This address is specific to the ddomain,
        even though it's available on the IMailingListAddresses interface.
        Generally, humans should never respond directly to this address.
        """)

    owner_address = Attribute(
        """The address which reaches the owners and moderators of the mailing
        list.  There is no address which reaches just the owners or just the
        moderators of a mailing list.
        """)

    request_address = Attribute(
        """The address which reaches the email robot for this mailing list.
        This robot can process various email commands such as changing
        delivery options, getting information or help about the mailing list,
        or processing subscrptions and unsubscriptions (although for the
        latter two, it's better to use the join_address and leave_address.
        """)

    bounces_address = Attribute(
        """The address which reaches the automated bounce processor for this
        mailing list.  Generally, humans should never respond directly to this
        address.
        """)

    join_address = Attribute(
        """The address to which subscription requests should be sent.""")

    leave_address = Attribute(
        """The address to which unsubscription requests should be sent.""")

    subscribe_address = Attribute(
        """Deprecated address to which subscription requests may be sent.
        This address is provided for backward compatibility only.  See
        `join_address` for the preferred alias.
        """)

    unsubscribe_address = Attribute(
        """Deprecated address to which unsubscription requests may be sent.
        This address is provided for backward compatibility only.  See
        `leave_address` for the preferred alias.
        """)

    def confirm_address(cookie=''):
        """The address used for various forms of email confirmation."""

    # DMARC attributes.

    dmarc_mitigate_action = Attribute(
        """The mitigation to apply to messages from a DMARC matching domain.

        This is a  DMARCMitigateAction to be applied to messages From: a domain
        publishing DMARC p=reject or quarantine, and possibly unconditionally
        depending on the setting of dmarc_mitigate_unconditionally.
        """)

    dmarc_mitigate_unconditionally = Attribute(
        """Should DMARC mitigations apply unconditionally?

        A flag indicating whether to apply dmarc_mitigate_action to all
        messages, but only if dmarc_mitigate_action is other than reject or
        discard.
        """)

    dmarc_moderation_notice = Attribute(
        """Text to include in any DMARC rejected message.

        Rejection notices are sent when DMARCMitigateAction of reject applies.
        """)

    dmarc_wrapped_message_text = Attribute(
        """Additional MIME text to include in DMARC wrapped messages.

        This text is added as a separate text/plain MIME part preceding the
        original message part in the wrapped message when DMARCMitigateAction
        of wrap_message applies.
        """)

    # Rosters and subscriptions.

    owners = Attribute(
        """The IUser owners of this mailing list.

        This does not include the IUsers who are moderators but not owners of
        the mailing list.""")

    moderators = Attribute(
        """The IUser moderators of this mailing list.

        This does not include the IUsers who are owners but not moderators of
        the mailing list.""")

    administrators = Attribute(
        """The IUser administrators of this mailing list.

        This includes the IUsers who are both owners and moderators of the
        mailing list.""")

    nonmembers = Attribute(
        """A roster of all the nonmembers of the mailing list.""")

    members = Attribute(
        """A roster of all the members of the mailing list, regardless of
        whether they are to receive regular messages or digests, or whether
        they have their delivery disabled or not.""")

    regular_members = Attribute(
        """An roster of all the IMembers who are to receive regular postings
        (i.e. non-digests) from the mailing list, regardless of whether they
        have their delivery disabled or not.""")

    digest_members = Attribute(
        """A roster of all the IMembers who are to receive digests of postings
        to this mailing list, regardless of whether they have their deliver
        disabled or not, or of the type of digest they are to receive.""")

    subscription_policy = Attribute(
        """The policy for subscribing new members to the list.""")

    unsubscription_policy = Attribute(
        """The policy for unsubscribing members from the list.""")

    subscribers = Attribute(
        """An iterator over all IMembers subscribed to this list, with any
        role.
        """)

    def get_roster(role):
        """Return the appropriate roster for the given role.

        :param role: The requested roster's role.
        :type role: MemberRole
        :return: The requested roster.
        :rtype: Roster
        """

    def is_subscribed(subscriber, role=MemberRole.member):
        """Is the given address or user subscribed to the mailing list?

        :param subscriber: The address or user to check.
        :type subscriber: `IUser` or `IAddress`
        :param role: The role being checked (e.g. a member, owner, or
            moderator of a mailing list).
        :type role: `MemberRole`
        :return: A flag indicating whether the subscriber is already
            subscribed to the mailing list or not.
        """

    def subscribe(subscriber, role=MemberRole.member):
        """Subscribe the given address or user to the mailing list.

        :param subscriber: The address or user to subscribe to the mailing
            list.  The user's preferred address receives deliveries, if she
            has one, otherwise no address for the user appears in the rosters.
        :type subscriber: `IUser` or `IAddress`
        :param role: The role being subscribed to (e.g. a member, owner, or
            moderator of a mailing list).
        :type role: `MemberRole`
        :return: The member object representing the subscription.
        :rtype: `IMember`
        :raises AlreadySubscribedError: If the address or user is already
            subscribed to the mailing list with the given role.  Note however
            that it is possible to subscribe an address to a mailing list with
            a particular role, and also subscribe a user with a matching
            preferred address that is explicitly subscribed with the same role.
        """

    # Delivery.

    archive_policy = Attribute(
        """The policy for archiving messages to this mailing list.

        The value is an `ArchivePolicy` enum.  Use this to archive the mailing
        list publicly, privately, or not at all.
        """)

    last_post_at = Attribute(
        """The date and time a message was last posted to the mailing list.""")

    post_id = Attribute(
        """A monotonically increasing integer sequentially assigned to each
        list posting.""")

    personalize = Attribute(
        """The type of personalization that is applied to postings.""")

    reply_goes_to_list = Attribute(
        """Reply-To: header munging policy.""")

    # Digests.

    digests_enabled = Attribute(
        """Whether or not digests are enabled for this mailing list.""")

    digest_size_threshold = Attribute(
        """The maximum (approximate) size in kilobytes of the digest currently
        being collected.""")

    digest_send_periodic = Attribute(
        """Should a digest be sent by the `mailman send_digest` command even
        when the size threshold hasn't yet been met?""")

    digest_volume_frequency = Attribute(
        """How often should a new digest volume be started?""")

    digest_last_sent_at = Attribute(
        """The date and time a digest of this mailing list was last sent.""")

    volume = Attribute(
        """A monotonically increasing integer sequentially assigned to each
        new digest volume.  The volume number may be bumped either
        automatically (i.e. on a defined schedule) or manually.  When the
        volume number is bumped, the digest number is always reset to 1.""")

    next_digest_number = Attribute(
        """A sequence number for a specific digest in a given volume.  When
        the digest volume number is bumped, the digest number is reset to
        1.""")

    def send_one_last_digest_to(address, delivery_mode):
        """Make sure to send one last digest to an address.

        This is used when a person transitions from digest delivery to regular
        delivery and wants to make sure they don't miss anything.  By
        indicating that they'd like to receive one last digest, they will
        ensure continuity in receiving mailing lists posts.

        :param address: The address of the person receiving one last digest.
        :type address: `IAddress`
        :param delivery_mode: The type of digest to receive.
        :type delivery_mode: `DeliveryMode`
        """

    last_digest_recipients = Attribute(
        """An iterator over the addresses that should receive one last digest.

        Items are 2-tuples of (`IAddress`, `DeliveryMode`).  The one last
        digest recipients are cleared.
        """)

    # Autoresponses.

    autoresponse_grace_period = Attribute(
        """Time period (in days) between automatic responses.

        When this mailing list is set to send an auto-response for messages
        sent to mailing list posts, the mailing list owners, or the `-request`
        address, such reponses will not be sent to the same user more than
        once during the grace period.  Set to zero (or a negative value) for
        no grace period (i.e. auto-respond to every message).
        """)

    autorespond_owner = Attribute(
        """How should the mailing list automatically respond to messages sent
        to the -owner or -moderator address?

        Options are:
        * No response sent
        * Send a response and discard the original messge
        * Send a response and continue processing the original message
        """)

    autoresponse_owner_text = Attribute(
        """The text sent in an autoresponse to the owner or moderator.""")

    autorespond_postings = Attribute(
        """How should the mailing list automatically respond to messages sent
        to the list's posting address?

        Options are:
        * No response sent
        * Send a response and discard the original messge
        * Send a response and continue processing the original message
        """)

    autoresponse_postings_text = Attribute(
        """The text sent in an autoresponse to the list's posting address.""")

    autorespond_requests = Attribute(
        """How should the mailing list automatically respond to messages sent
        to the list's `-request` address?

        Options are:
        * No response sent
        * Send a response and discard the original messge
        * Send a response and continue processing the original message
        """)

    autoresponse_request_text = Attribute(
        """The text sent in an autoresponse to the list's `-request`
        address.""")

    # Processing.

    posting_chain = Attribute(
        """This mailing list's posting moderation chain.

        When messages are posted to a mailing list, it first goes through a
        moderation chain to determine whether the message will be accepted.
        This attribute names a chain for postings, which must exist.
        """)

    posting_pipeline = Attribute(
        """This mailing list's posting pipeline.

        Every mailing list has a processing pipeline that messages flow
        through once they've been accepted for posting to the mailing list.
        This attribute names a pipeline for postings, which must exist.
        """)

    owner_chain = Attribute(
        """This mailing list's owner moderation chain.

        When messages are posted to the owners of a mailing list, it first
        goes through a moderation chain to determine whether the message will
        be accepted.  This attribute names a chain for postings, which must
        exist.
        """)

    owner_pipeline = Attribute(
        """This mailing list's owner posting pipeline.

        Every mailing list has a processing pipeline that messages flow
        through once they've been accepted for posting to the owners of a
        mailing list.  This attribute names a pipeline for postings, which
        must exist.
        """)

    data_path = Attribute(
        """The file system path to list-specific data.

        An example of list-specific data is the temporary digest mbox file
        that gets created to accumlate messages for the digest.
        """)

    administrivia = Attribute(
        """Flag controlling `administrivia` checks.

        Administrivia tests check whether postings to the mailing list are
        really meant for the -request address.  Examples include messages with
        `help`, `subscribe`, `unsubscribe`, and other commands.  When such
        messages are incorrectly posted to the general mailing list, they are
        just noise, and when this flag is set will be intercepted and in
        general held for moderator approval.
        """)

    filter_content = Attribute(
        """Flag specifying whether to filter a message's content.

        Filtering is performed on MIME type and file name extension.
        """)

    filter_action = Attribute(
        """Action to take when the top-level content-type is filtered.

        The value is a `FilterAction` enum.
        """)

    convert_html_to_plaintext = Attribute(
        """Flag specifying whether text/html parts should be converted.

        When True, after filtering, if there are any text/html parts left in
        the original message, they are converted to text/plain.
        """)

    collapse_alternatives = Attribute(
        """Flag specifying whether multipart/alternatives should be collapsed.

        After all MIME content filtering is complete, collapsing alternatives
        replaces the outer multipart/alternative parts with the first
        subpart.
        """)

    filter_types = Attribute(
        """Sequence of MIME types that should be filtered out.

        These can be either main types or main/sub types.  Set this attribute
        to a sequence to change it, or to None to empty it.
        """)

    pass_types = Attribute(
        """Sequence of MIME types to explicitly pass.

        These can be either main types or main/sub types.  Set this attribute
        to a sequence to change it, or to None to empty it.  Pass types are
        consulted after filter types, and only if `pass_types` is non-empty.
        """)

    filter_extensions = Attribute(
        """Sequence of file extensions that should be filtered out.

        Set this attribute to a sequence to change it, or to None to empty it.
        """)

    pass_extensions = Attribute(
        """Sequence of file extensions to explicitly pass.

        Set this attribute to a sequence to change it, or to None to empty it.
        Pass extensions are consulted after filter extensions, and only if
        `pass_extensions` is non-empty.
        """)

    # Moderation.

    default_member_action = Attribute(
        """The default action to take for postings from members.

        When an address is subscribed to the mailing list, this attribute sets
        the initial moderation action (as an `Action`).  When the action is
        `Action.defer` (the default), then normal posting decisions are made.
        When the action is `Action.accept`, the postings are accepted without
        any other checks.
        """)

    default_nonmember_action = Attribute(
        """The default action to take for postings from nonmembers.

        When a nonmember address posts to the mailing list, this attribute
        sets the initial moderation action (as an `Action`).  When the action
        is `Action.defer` (the default), then normal posting decisions are
        made.  When the action is `Action.accept`, the postings are accepted
        without any other checks.
        """)

    newsgroup_moderation = Attribute(
        """The moderation policy for the linked newsgroup, if there is one.""")

    # Bounces.

    forward_unrecognized_bounces_to = Attribute(
        """What to do when a bounce contains no recognizable addresses.

        This is an enumeration which specifies what to do with such bounce
        messages.  They can be discarded, forward to the list owner, or
        forwarded to the site owner.
        """)

    process_bounces = Attribute(
        """Whether or not the mailing list processes bounces.""")

    # Notifications.

    admin_immed_notify = Attribute(
        """Flag controlling immediate notification of requests.

        List moderators normally get daily notices about pending
        administrative requests.  This flag controls whether moderators also
        receive immediate notification of such pending requests.
        """)

    admin_notify_mchanges = Attribute(
        """Flag controlling notification of joins and leaves.

        List moderators can receive notifications for every member that joins
        or leaves their mailing lists.  This flag controls those
        notifications.
        """)

    send_welcome_message = Attribute(
        """Flag indicating whether a welcome message should be sent.""")

    send_goodbye_message = Attribute(
        """Flag indicating whether a goodbye message should be sent.""")


@public
class IAcceptableAlias(Interface):
    """An acceptable alias for implicit destinations."""

    mailing_list = Attribute('The associated mailing list.')

    address = Attribute('The address or pattern to match against recipients.')


@public
class IAcceptableAliasSet(Interface):
    """The set of acceptable aliases for a mailing list."""

    def clear():
        """Clear the set of acceptable posting aliases."""

    def add(alias):
        """Add the given address as an acceptable aliases for posting.

        :param alias: The email address to accept as a recipient for implicit
            destination posting purposes.  The alias is coerced to lower
            case.  If `alias` begins with a '^' character, it is interpreted
            as a regular expression, otherwise it must be an email address.
        :type alias: string
        :raises ValueError: when the alias neither starts with '^' nor has an
            '@' sign in it.
        """

    def remove(alias):
        """Remove the given address as an acceptable aliases for posting.

        :param alias: The email address to no longer accept as a recipient for
            implicit destination posting purposes.
        :type alias: string
        """

    aliases = Attribute(
        """An iterator over all the acceptable aliases.""")


@public
class IListArchiver(Interface):
    """An archiver for a mailing list.

    The named archiver must be enabled site-wide in order for a mailing list
    to be able to enable it.
    """

    mailing_list = Attribute('The associated mailing list.')

    name = Attribute('The name of the archiver.')

    is_enabled = Attribute('Is this archiver enabled for this mailing list?')

    system_archiver = Attribute(
        'The associated system-wide IArchiver instance.')


@public
class IListArchiverSet(Interface):
    """The set of archivers (enabled or disabled) for a mailing list."""

    archivers = Attribute(
        """An iterator over all the archivers for this mailing list.""")

    def get(archiver_name):
        """Return the `IListArchiver` with the given name, if it exists.

        :param archiver_name: The name of the archiver.
        :type archiver_name: unicode.
        :return: the matching `IListArchiver` or None if the named archiver
            does not exist.
        """


@public
class IHeaderMatch(Interface):
    """A mailing list-specific message header matching rule."""

    mailing_list = Attribute(
        """The mailing list for the header match.""")

    header = Attribute(
        """The email header that will be checked.""")

    pattern = Attribute(
        """The regular expression to match.""")

    position = Attribute(
        """The ordinal position of this header match.

        Set this to change the position of this header match.
        """)

    chain = Attribute(
        """The chain to jump to on a match.

        If it is None, the `[antispam]jump_chain` action in the configuration
        file is used.
        """)


@public
class IHeaderMatchList(Interface):
    """The list of header matching rules for a mailing list."""

    def clear():
        """Clear the list of header matching rules."""

    def append(header, pattern, chain=None):
        """Append the given rule to this mailing list's header match list.

        :param header: The email header to filter on.  It will be converted to
            lower case for consistency.
        :type header: string
        :param pattern: The regular expression to use.
        :type pattern: string
        :param chain: The chain to jump to, or None to use the site-wide
            antispam jump chain via the configuration.  Defaults to None.
        :type chain: string or None
        :raises ValueError: if the header/pattern pair already exists for this
            mailing list.
        """

    def insert(index, header, pattern, chain=None):
        """Insert a header match rule.

        Inserts the given rule at the given index position in this
        mailing list's header match list.

        :param index: The index to insert the rule at.
        :type index: integer
        :param header: The email header to filter on.  It will be converted to
            lower case for consistency.
        :type header: string
        :param pattern: The regular expression to use.
        :type pattern: string
        :param chain: The chain to jump to, or None to use the site-wide
            antispam jump chain via the configuration.  Defaults to None.
        :type chain: string or None
        :raises ValueError: if the header/pattern pair already exists for this
            mailing list.
        """

    def remove(header, pattern):
        """Remove the given rule from this mailing list's header match list.

        :param header: The email header part of the rule to be removed.
        :type header: string
        :param pattern: The regular expression part of the rule to be removed.
        :type pattern: string
        :raises ValueError: if the header does not exist in the list of
            header matches.
        """

    def __getitem__(index):
        """Return the header match at the given index for this mailing list.

        :param index: The index of the header match to return.
        :type index: integer
        :return: The header match at this index.
        :rtype: `IHeaderMatch`
        :raises IndexError: if there is no header match at this index for
            this mailing list.
        """

    def __delitem__(index):
        """Remove the rule at the given index.

        :param index: The index of the header match to remove.
        :type index: integer
        :raises IndexError: if there is no header match at this index for
            this mailing list.
        """

    def __len__():
        """Return the number of header matches for this mailing list.

        :rtype: integer
        """

    def __iter__():
        """An iterator over all the IHeaderMatches defined in this list.

        :return: iterator over `IHeaderMatch`.
        """
