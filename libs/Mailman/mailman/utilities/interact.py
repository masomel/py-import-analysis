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

"""Provide an interactive prompt, mimicking the Python interpreter."""

import os
import sys
import code

from contextlib import suppress
from inspect import signature
from public import public


DEFAULT_BANNER = object()


@public
def interact(upframe=True, banner=DEFAULT_BANNER, overrides=None):
    """Start an interactive interpreter prompt.

    :param upframe: Whether or not to populate the interpreter's globals with
        the locals from the frame that called this function.
    :type upframe: bool
    :param banner: The banner to print before the interpreter starts.
    :type banner: string
    :param overrides: Additional interpreter globals to add.
    :type overrides: dict
    """
    # The interactive prompt's namespace.
    namespace = dict()
    # Populate the console's with the locals of the frame that called this
    # function (i.e. one up from here).
    if upframe:
        frame = sys._getframe(1)
        namespace.update(frame.f_globals)
        namespace.update(frame.f_locals)
    if overrides is not None:
        namespace.update(overrides)
    interp = code.InteractiveConsole(namespace)
    # Try to import the readline module, but don't worry if it's unavailable.
    with suppress(ImportError):
        import readline                             # noqa: F401
    # Mimic the real interactive interpreter's loading of any $PYTHONSTARTUP
    # file.  Note that if the startup file is not prepared to be exec'd more
    # than once, this could cause a problem.
    startup = os.environ.get('PYTHONSTARTUP')
    if startup:
        with open(startup, 'r', encoding='utf-8') as fp:
            interp.runcode(compile(fp.read(), startup, 'exec'))
    # We don't want the funky console object in parentheses in the banner.
    if banner is DEFAULT_BANNER:
        banner = '''\
Python %s on %s
Type "help", "copyright", "credits" or "license" for more information.''' % (
            sys.version, sys.platform)
    # Python 3.6 added an exitmsg keyword but we don't currently support
    # configuring it.  For consistency between Python 3.6 and earlier
    # versions, suppress the exit message if possible.
    kws = dict(banner=banner)
    if 'exitmsg' in signature(interp.interact).parameters:
        kws['exitmsg'] = ''
    interp.interact(**kws)
