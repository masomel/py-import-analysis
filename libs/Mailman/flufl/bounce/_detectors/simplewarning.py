"""Recognizes simple heuristically delimited warnings."""

from flufl.bounce._detectors.simplematch import SimpleMatch, _c
from flufl.bounce.interfaces import NoPermanentFailures
from public import public


# This is a list of tuples of the form
#
#     (start cre, end cre, address cre)
#
# where 'cre' means compiled regular expression, start is the line just before
# the bouncing address block, end is the line just after the bouncing address
# block, and address cre is the regexp that will recognize the addresses.  It
# must have a group called 'addr' which will contain exactly and only the
# address that bounced.
PATTERNS = [
    # pop3.pta.lia.net
    (_c('The address to which the message has not yet been delivered is'),
     _c('No action is required on your part'),
     _c(r'\s*(?P<addr>\S+@\S+)\s*')),
    # MessageSwitch
    (_c('Your message to:'),
     _c('This is just a warning, you do not need to take any action'),
     _c(r'\s*(?P<addr>\S+@\S+)\s*')),
    # Symantec_AntiVirus_for_SMTP_Gateways
    (_c('Your message with Subject:'),
     _c('Delivery attempts will continue to be made'),
     _c(r'\s*(?P<addr>\S+@\S+)\s*')),
    # googlemail.com warning
    (_c('Delivery to the following recipient has been delayed'),
     _c('Message will be retried'),
     _c(r'\s*(?P<addr>\S+@\S+)\s*')),
    # Exchange warning message.
    (_c('This is an advisory-only email'),
     _c('has been postponed'),
     _c('"(?P<addr>[^"]+)"')),
    # kundenserver.de
    (_c('not yet been delivered'),
     _c('No action is required on your part'),
     _c(r'\s*<?(?P<addr>\S+@[^>\s]+)>?\s*')),
    # Next one goes here...
    ]


@public
class SimpleWarning(SimpleMatch):
    """Recognizes simple heuristically delimited warnings."""

    PATTERNS = PATTERNS

    def process(self, msg):
        """See `SimpleMatch`."""
        # Since these are warnings, they're classified as temporary failures.
        # There are no permanent failures.
        (temporary,
         permanent_really_temporary) = super(SimpleWarning, self).process(msg)
        return permanent_really_temporary, NoPermanentFailures
