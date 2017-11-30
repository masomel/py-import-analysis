"""Catalog search strategies."""

import os
import gettext

from public import public


class _BaseStrategy:
    """Common code for strategies."""

    def __init__(self, name):
        """Create a catalog lookup strategy.

        :param name: The application's name.
        :type name: string
        """
        self.name = name
        self._messages_dir = None

    def __call__(self, language_code=None):
        """Find the catalog for the language.

        :param language_code: The language code to find.  If None, then the
            default gettext language code lookup scheme is used.
        :type language_code: string
        :return: A `gettext` catalog.
        :rtype: `gettext.NullTranslations` or subclass
        """
        # gettext.translation() requires None or a sequence.
        languages = (None if language_code is None else [language_code])
        try:
            return gettext.translation(
                self.name, self._messages_dir, languages)
        except IOError:
            # Fall back to untranslated source language.
            return gettext.NullTranslations()


@public
class PackageStrategy(_BaseStrategy):
    """A strategy that finds catalogs based on package paths."""

    def __init__(self, name, package):
        """Create a catalog lookup strategy.

        :param name: The application's name.
        :type name: string
        :param package: The package path to the message catalogs.  This
            strategy uses the __file__ of the package path as the directory
            containing `gettext` messages.
        :type package_name: module
        """
        super().__init__(name)
        self._messages_dir = os.path.dirname(package.__file__)


@public
class SimpleStrategy(_BaseStrategy):
    """A simpler strategy for getting translations."""

    def __init__(self, name):
        """Create a catalog lookup strategy.

        :param name: The application's name.
        :type name: string
        :param package: The package path to the message catalogs.  This
            strategy uses the __file__ of the package path as the directory
            containing `gettext` messages.
        :type package_name: module
        """
        super().__init__(name)
        self._messages_dir = os.environ.get('LOCPATH')
