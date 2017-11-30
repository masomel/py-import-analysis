# Copyright (C) 2007-2017 by the Free Software Foundation, Inc.
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

"""Harness for testing Mailman's documentation.

Note that doctest extraction does not currently work for zip file
distributions.  doctest discovery currently requires file system traversal.
"""

from contextlib import ExitStack
from mailman.app.lifecycle import create_list
from mailman.config import config
from mailman.testing.helpers import (
    call_api, get_queue_messages, specialized_message_from_string, subscribe)
from mailman.testing.layers import SMTPLayer
from public import public


DOT = '.'
COMMASPACE = ', '


def stop():
    """Call into pdb.set_trace()"""
    # Do the import here so that you get the wacky special hacked pdb instead
    # of Python's normal pdb.
    import pdb
    pdb.set_trace()


def dump_msgdata(msgdata, *additional_skips):
    """Dump in a more readable way a message metadata dictionary."""
    if len(msgdata) == 0:
        print('*Empty*')
        return
    skips = set(additional_skips)
    # Some stuff we always want to skip, because their values will always be
    # variable data.
    skips.add('received_time')
    longest = max(len(key) for key in msgdata if key not in skips)
    for key in sorted(msgdata):
        if key in skips:
            continue
        print('{0:{2}}: {1}'.format(key, msgdata[key], longest))


def dump_list(list_of_things, key=str):
    """Print items in a string to get rid of stupid u'' prefixes."""
    # List of things may be a generator.
    list_of_things = list(list_of_things)
    if len(list_of_things) == 0:
        print('*Empty*')
    if key is not None:
        list_of_things = sorted(list_of_things, key=key)
    for item in list_of_things:
        print(item)


def call_http(url, data=None, method=None, username=None, password=None):
    """'Call a URL with a given HTTP method and return the resulting object.

    The object will have been JSON decoded.

    :param url: The url to open, read, and print.
    :type url: string
    :param data: Data to use to POST to a URL.
    :type data: dict
    :param method: Alternative HTTP method to use.
    :type method: str
    :param username: The HTTP Basic Auth user name.  None means use the value
        from the configuration.
    :type username: str
    :param password: The HTTP Basic Auth password.  None means use the value
        from the configuration.
    :type username: str
    :return: The decoded JSON data structure.
    :raises HTTPError: when a non-2xx return code is received.
    """
    content, response = call_api(url, data, method, username, password)
    if content is None:
        # We used to use httplib2 here, which included the status code in the
        # response headers in the `status` key.  requests doesn't do this, but
        # the doctests expect it so for backward compatibility, include the
        # status code in the printed response.
        headers = dict(status=response.status_code)
        headers.update({
            field.lower(): response.headers[field]
            for field in response.headers
            })
        for field in sorted(headers):
            print('{}: {}'.format(field, headers[field]))
        return None
    return content


def dump_json(url, data=None, method=None, username=None, password=None):
    """Print the JSON dictionary read from a URL.

    :param url: The url to open, read, and print.
    :type url: string
    :param data: Data to use to POST to a URL.
    :type data: dict
    :param method: Alternative HTTP method to use.
    :type method: str
    :param username: The HTTP Basic Auth user name.  None means use the value
        from the configuration.
    :type username: str
    :param password: The HTTP Basic Auth password.  None means use the value
        from the configuration.
    :type username: str
    """
    results = call_http(url, data, method, username, password)
    if results is None:
        return
    for key in sorted(results):
        value = results[key]
        if key == 'entries':
            for i, entry in enumerate(value):
                # entry is a dictionary.
                print('entry %d:' % i)
                for entry_key in sorted(entry):
                    print('    {}: {}'.format(entry_key, entry[entry_key]))
        elif isinstance(value, list):
            printable_value = COMMASPACE.join(
                "'{}'".format(s) for s in sorted(value))
            print('{}: [{}]'.format(key, printable_value))
        else:
            print('{}: {}'.format(key, value))


@public
def setup(testobj):
    """Test setup."""
    # In general, I don't like adding convenience functions, since I think
    # doctests should do the imports themselves.  It makes for better
    # documentation that way.  However, a few are really useful, or help to
    # hide some icky test implementation details.
    testobj.globs['call_http'] = call_http
    testobj.globs['config'] = config
    testobj.globs['create_list'] = create_list
    testobj.globs['dump_json'] = dump_json
    testobj.globs['dump_msgdata'] = dump_msgdata
    testobj.globs['dump_list'] = dump_list
    testobj.globs['get_queue_messages'] = get_queue_messages
    testobj.globs['message_from_string'] = specialized_message_from_string
    testobj.globs['smtpd'] = SMTPLayer.smtpd
    testobj.globs['stop'] = stop
    testobj.globs['subscribe'] = subscribe
    testobj.globs['transaction'] = config.db
    # Add this so that cleanups can be automatically added by the doctest.
    testobj.globs['cleanups'] = ExitStack()


@public
def teardown(testobj):
    testobj.globs['cleanups'].close()
