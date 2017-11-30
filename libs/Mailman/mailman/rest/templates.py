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

"""Template finder."""

from mailman.rest.helpers import not_found
from mailman.utilities.i18n import TemplateNotFoundError, find
from public import public


# Use mimetypes.guess_all_extensions()?
EXTENSIONS = {
    'text/plain': '.txt',
    'text/html': '.html',
    }


@public
class TemplateFinder:
    """Template finder resource."""

    def __init__(self, mlist, template, language, content_type):
        self.mlist = mlist
        self.template = template
        self.language = language
        self.content_type = content_type

    def on_get(self, request, response):
        # XXX We currently only support .txt and .html files.
        extension = EXTENSIONS.get(self.content_type)
        if extension is None:
            not_found(response)
            return
        template = self.template + extension
        fp = None
        try:
            try:
                path, fp = find(template, self.mlist, self.language)
            except TemplateNotFoundError:
                not_found(response)
                return
            else:
                return fp.read()
        finally:
            if fp is not None:
                fp.close()
