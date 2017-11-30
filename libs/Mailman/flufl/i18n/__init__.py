"""Expose sub-module names in the package namespace."""

from flufl.i18n._application import Application     # noqa: F401
from flufl.i18n._expand import expand               # noqa: F401
from flufl.i18n._registry import registry
from flufl.i18n._strategy import *                  # noqa: F403
from public import public


__version__ = '2.0'


@public
def initialize(domain):
    """A convenience function for setting up translation.

    :param domain: The application's name.
    :type domain: string
    """
    strategy = SimpleStrategy(domain)               # noqa: F405
    application = registry.register(strategy)
    return application._
