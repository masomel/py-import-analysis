"""String interpolation."""

import logging

from public import public
from string import Template


log = logging.getLogger('flufl.i18n')


@public
def expand(template, substitutions, template_class=Template):
    """Expand string template with substitutions.

    :param template: A PEP 292 $-string template.
    :type template: string
    :param substitutions: The substitutions dictionary.
    :type substitutions: dict
    :param template_class: The template class to use.
    :type template_class: class
    :return: The substituted string.
    :rtype: string
    """
    try:
        return template_class(template).safe_substitute(substitutions)
    except (TypeError, ValueError):
        # The template is really screwed up.
        log.exception('broken template: %s', template)
