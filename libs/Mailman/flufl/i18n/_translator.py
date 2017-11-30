"""Basic translation context class."""

import sys
import textwrap

from flufl.i18n._expand import expand
from flufl.i18n._substitute import Template, attrdict
from public import public


@public
class Translator:
    """A translation context."""

    def __init__(self, catalog, dedent=True, depth=2):
        """Create a translation context.

        :param catalog: The translation catalog.
        :type catalog: `gettext.NullTranslations` or subclass
        :param dedent: Whether the input string should be dedented.
        :type dedent: bool
        :param depth: Number of stack frames to call sys._getframe() with.
        :type depth: int
        """
        self._catalog = catalog
        self.dedent = dedent
        self.depth = depth

    def translate(self, original, extras=None):
        """Translate the string.

        :param original: The original string to translate.
        :type original: string
        :param extras: Extra substitution mapping, elements of which override
            the locals and globals.
        :return: The translated string.
        :rtype: string
        """
        if original == '':
            return ''
        assert original, 'Cannot translate: {}'.format(original)
        # Because the original string is what the text extractors put into the
        # catalog, we must first look up the original unadulterated string in
        # the catalog.  Use the global translation context for this.
        #
        # Translations must be unicode safe internally.  The translation
        # service is one boundary to the outside world, so to honor this
        # constraint, make sure that all strings to come out of this are
        # unicodes, even if the translated string or dictionary values are
        # 8-bit strings.
        tns = self._catalog.gettext(original)
        # Do PEP 292 style $-string interpolation into the resulting string.
        #
        # This lets you write something like:
        #
        #     now = time.ctime(time.time())
        #     print _('The current time is: $now')
        #
        # and have it Just Work.  Key precedence is:
        #
        #     extras > locals > globals
        #
        # Get the frame of the caller.
        frame = sys._getframe(self.depth)
        # Create the raw dictionary of substitutions.
        raw_dict = frame.f_globals.copy()
        raw_dict.update(frame.f_locals)
        if extras is not None:
            raw_dict.update(extras)
        # Python 2 requires ** dictionaries to have str, not unicode keys.
        # For our purposes, keys should always be ascii.  Values though should
        # be unicode.
        translated_string = expand(tns, attrdict(raw_dict), Template)
        # Dedent the string if so desired.
        if self.dedent:
            translated_string = textwrap.dedent(translated_string)
        return translated_string
