# Copyright (C) 2015-2017 by the Free Software Foundation, Inc.
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

"""A fake MHonArc process that reads stdin and writes stdout."""

import sys

from email import message_from_string


def main():
    text = sys.stdin.read()
    msg = message_from_string(text)
    output_file = sys.argv[1]
    with open(output_file, 'w', encoding='utf-8') as fp:
        print(msg['message-id'], file=fp)
        print(msg['message-id-hash'], file=fp)


if __name__ == '__main__':
    main()
