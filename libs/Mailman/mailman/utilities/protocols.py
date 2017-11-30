# Copyright (C) 2016-2017 by the Free Software Foundation, Inc.
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

"""Various URL protocol support."""

import requests

from mailman.interfaces.languages import ILanguageManager
from mailman.interfaces.listmanager import IListManager
from mailman.utilities.i18n import TemplateNotFoundError, find
from public import public
from urllib.error import URLError
from urllib.parse import urlparse
from zope.component import getUtility

COMMASPACE = ', '


@public
def get(url, **kws):
    parsed = urlparse(url)
    if parsed.scheme in ('http', 'https'):
        response = requests.get(url, **kws)
        response.raise_for_status()
        return response.text
    if parsed.scheme == 'file':
        mode = kws.pop('mode', 'r')
        arguments = dict(mode=mode)
        if 'encoding' in kws or 'b' not in mode:
            arguments['encoding'] = kws.pop('encoding', 'utf-8')
        if len(kws) > 0:
            raise ValueError('Unexpected arguments: {}'.format(
                COMMASPACE.join(sorted(kws))))
        with open(parsed.path, **arguments) as fp:
            return fp.read()
    if parsed.scheme == 'mailman':
        mlist = code = None
        if len(kws) > 0:
            raise ValueError('Unexpected arguments: {}'.format(
                COMMASPACE.join(sorted(kws))))
        # The path can contain one, two, or three components.  Since no empty
        # path components are legal, filter them out.
        parts = [p for p in parsed.path.split('/') if p]
        if len(parts) == 0:
            raise URLError('No template specified')
        elif len(parts) == 1:
            template = parts[0]
        elif len(parts) == 2:
            part0, template = parts
            # Is part0 a language code or a mailing list?  This is rather
            # tricky because if it's a mailing list, it could be a list-id and
            # that will contain dots, as could the language code.
            language = getUtility(ILanguageManager).get(part0)
            if language is None:
                list_manager = getUtility(IListManager)
                # part0 must be a fqdn-listname or list-id.
                mlist = (list_manager.get(part0)
                         if '@' in part0 else
                         list_manager.get_by_list_id(part0))
                if mlist is None:
                    raise URLError('Bad language or list name')
            else:
                code = language.code
        elif len(parts) == 3:
            part0, code, template = parts
            # part0 could be an fqdn-listname or a list-id.
            mlist = (getUtility(IListManager).get(part0)
                     if '@' in part0 else
                     getUtility(IListManager).get_by_list_id(part0))
            if mlist is None:
                raise URLError('Missing list')
            language = getUtility(ILanguageManager).get(code)
            if language is None:
                raise URLError('No such language')
            code = language.code
        else:
            raise URLError('No such file')
        # Find the template, mutating any missing template exception.
        try:
            path, fp = find(template, mlist, code)
        except TemplateNotFoundError:
            raise URLError('No such file')
        try:
            return fp.read()
        finally:
            fp.close()
    raise URLError(url)
