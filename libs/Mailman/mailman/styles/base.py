# Copyright (C) 2012-2017 by the Free Software Foundation, Inc.
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

"""Building blocks for styles.

Use these to compose higher level styles.  Their apply() methods deliberately
have no super() upcall.  You need to explicitly call all base class apply()
methods in your compositional derived class.
"""


from datetime import timedelta
from mailman.core.i18n import _
from mailman.interfaces.action import Action, FilterAction
from mailman.interfaces.archiver import ArchivePolicy
from mailman.interfaces.autorespond import ResponseAction
from mailman.interfaces.bounce import UnrecognizedBounceDisposition
from mailman.interfaces.digests import DigestFrequency
from mailman.interfaces.mailinglist import (
    DMARCMitigateAction, Personalization, ReplyToMunging, SubscriptionPolicy)
from mailman.interfaces.nntp import NewsgroupModeration
from public import public


@public
class Identity:
    """Set basic identify attributes."""

    def apply(self, mailing_list):
        # For cut-n-paste convenience.
        mlist = mailing_list
        mlist.display_name = mlist.list_name.capitalize()
        mlist.include_rfc2369_headers = True
        mlist.volume = 1
        mlist.post_id = 1
        mlist.description = ''
        mlist.info = ''
        mlist.preferred_language = 'en'
        mlist.subject_prefix = _('[$mlist.display_name] ')
        mlist.encode_ascii_prefixes = (
            mlist.preferred_language.charset != 'us-ascii')


@public
class BasicOperation:
    """Set basic operational attributes."""

    def apply(self, mailing_list):
        # For cut-n-paste convenience.
        mlist = mailing_list
        mlist.emergency = False
        mlist.personalize = Personalization.none
        mlist.default_member_action = Action.defer
        mlist.default_nonmember_action = Action.hold
        mlist.subscription_policy = SubscriptionPolicy.confirm
        mlist.unsubscription_policy = SubscriptionPolicy.confirm
        # Notify the administrator of pending requests and membership changes.
        mlist.admin_immed_notify = True
        mlist.admin_notify_mchanges = False
        mlist.respond_to_post_requests = True
        mlist.obscure_addresses = True
        mlist.collapse_alternatives = True
        mlist.convert_html_to_plaintext = False
        mlist.filter_action = FilterAction.discard
        mlist.filter_content = False
        # Digests.
        mlist.digests_enabled = True
        mlist.digest_is_default = False
        mlist.mime_is_default_digest = False
        mlist.digest_size_threshold = 30          # KB
        mlist.digest_send_periodic = True
        mlist.digest_volume_frequency = DigestFrequency.monthly
        mlist.next_digest_number = 1
        # DMARC
        mlist.dmarc_mitigate_action = DMARCMitigateAction.no_mitigation
        mlist.dmarc_mitigate_unconditionally = False
        mlist.dmarc_moderation_notice = ''
        mlist.dmarc_wrapped_message_text = ''
        # NNTP gateway
        mlist.nntp_host = ''
        mlist.linked_newsgroup = ''
        mlist.gateway_to_news = False
        mlist.gateway_to_mail = False
        mlist.nntp_prefix_subject_too = True
        # In patch #401270, this was called newsgroup_is_moderated, but the
        # semantics weren't quite the same.
        mlist.newsgroup_moderation = NewsgroupModeration.none
        # Topics
        #
        # `topics' is a list of 4-tuples of the following form:
        #
        #     (name, pattern, description, emptyflag)
        #
        # name is a required arbitrary string displayed to the user when they
        # get to select their topics of interest
        #
        # pattern is a required verbose regular expression pattern which is
        # used as IGNORECASE.
        #
        # description is an optional description of what this topic is
        # supposed to match
        #
        # emptyflag is a boolean used internally in the admin interface to
        # signal whether a topic entry is new or not (new ones which do not
        # have a name or pattern are not saved when the submit button is
        # pressed).
        mlist.topics = []
        mlist.topics_enabled = False
        mlist.topics_bodylines_limit = 5
        # This is a mapping between user "names" (i.e. addresses) and
        # information about which topics that user is interested in.  The
        # values are a list of topic names that the user is interested in,
        # which should match the topic names in mlist.topics above.
        #
        # If the user has not selected any topics of interest, then the rule
        # is that they will get all messages, and they will not have an entry
        # in this dictionary.
        mlist.topics_userinterest = {}
        # scrub regular delivery
        mlist.scrub_nondigest = False


@public
class Bounces:
    """Basic bounce processing."""

    def apply(self, mailing_list):
        # For cut-n-paste convenience.
        mlist = mailing_list
        # Bounces
        mlist.forward_unrecognized_bounces_to = (
            UnrecognizedBounceDisposition.administrators)
        mlist.process_bounces = True
        mlist.bounce_score_threshold = 5.0
        mlist.bounce_info_stale_after = timedelta(days=7)
        mlist.bounce_you_are_disabled_warnings = 3
        mlist.bounce_you_are_disabled_warnings_interval = timedelta(days=7)
        mlist.bounce_notify_owner_on_disable = True
        mlist.bounce_notify_owner_on_removal = True
        # Autoresponder
        mlist.autorespond_owner = ResponseAction.none
        mlist.autoresponse_owner_text = ''
        mlist.autorespond_postings = ResponseAction.none
        mlist.autoresponse_postings_text = ''
        mlist.autorespond_requests = ResponseAction.none
        mlist.autoresponse_request_text = ''
        mlist.autoresponse_grace_period = timedelta(days=90)
        # This holds legacy member related information.  It's keyed by the
        # member address, and the value is an object containing the bounce
        # score, the date of the last received bounce, and a count of the
        # notifications left to send.
        mlist.bounce_info = {}
        # New style delivery status
        mlist.delivery_status = {}
        # The processing chain that messages posted to this mailing list get
        # processed by.
        mlist.posting_chain = 'default-posting-chain'
        # The default pipeline to send accepted messages through to the
        # mailing list's members.
        mlist.posting_pipeline = 'default-posting-pipeline'
        # The processing chain that messages posted to this mailing list's
        # -owner address gets processed by.
        mlist.owner_chain = 'default-owner-chain'
        # The default pipeline to send -owner email through.
        mlist.owner_pipeline = 'default-owner-pipeline'


@public
class Public:
    """Settings for public mailing lists."""

    def apply(self, mailing_list):
        # For cut-n-paste convenience.
        mlist = mailing_list
        mlist.advertised = True
        mlist.reply_goes_to_list = ReplyToMunging.no_munging
        mlist.reply_to_address = ''
        mlist.first_strip_reply_to = False
        mlist.archive_policy = ArchivePolicy.public


@public
class Announcement:
    """Settings for announce-only lists."""

    def apply(self, mailing_list):
        # For cut-n-paste convenience.
        mlist = mailing_list
        mlist.allow_list_posts = False
        mlist.send_welcome_message = True
        mlist.send_goodbye_message = True
        mlist.anonymous_list = False


@public
class Discussion:
    """Settings for standard discussion lists."""

    def apply(self, mailing_list):
        # For cut-n-paste convenience.
        mlist = mailing_list
        mlist.allow_list_posts = True
        mlist.send_welcome_message = True
        mlist.send_goodbye_message = True
        mlist.anonymous_list = False


@public
class Moderation:
    """Settings for basic moderation."""

    def apply(self, mailing_list):
        # For cut-n-paste convenience.
        mlist = mailing_list
        mlist.max_num_recipients = 10
        mlist.max_message_size = 40               # KB
        mlist.require_explicit_destination = True
        mlist.bounce_matching_headers = """
# Lines that *start* with a '#' are comments.
to: friend@public.com
message-id: relay.comanche.denmark.eu
from: list@listme.com
from: .*@uplinkpro.com
"""
        mlist.header_matches = []
        mlist.administrivia = True
        # Member moderation.
        mlist.member_moderation_notice = ''
        mlist.accept_these_nonmembers = []
        mlist.hold_these_nonmembers = []
        mlist.reject_these_nonmembers = []
        mlist.discard_these_nonmembers = []
        mlist.forward_auto_discards = True
        mlist.nonmember_rejection_notice = ''
        # automatic discarding
        mlist.max_days_to_hold = 0
