"""Parse bounce messages generated by Exim.

Exim adds an X-Failed-Recipients: header to bounce messages containing
an `addresslist' of failed addresses.
"""

from email.utils import getaddresses
from flufl.bounce.interfaces import IBounceDetector, NoTemporaryFailures
from public import public
from zope.interface import implementer


@public
@implementer(IBounceDetector)
class Exim:
    """Parse bounce messages generated by Exim."""

    def process(self, msg):
        """See `IBounceDetector`."""
        all_failed = msg.get_all('x-failed-recipients', [])
        # all_failed will contain string/unicode values, but the flufl.bounce
        # API requires these to be bytes.  We don't know the encoding, but
        # assume it must be ascii, per the relevant RFCs.
        return (NoTemporaryFailures,
                set(address.encode('us-ascii')
                    for name, address in getaddresses(all_failed)))
