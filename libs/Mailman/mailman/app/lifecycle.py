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

"""Application level list creation."""

import re
import shutil
import logging

from contextlib import suppress
from mailman.config import config
from mailman.interfaces.address import IEmailValidator
from mailman.interfaces.domain import (
    BadDomainSpecificationError, IDomainManager)
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.mailinglist import InvalidListNameError
from mailman.interfaces.member import MemberRole
from mailman.interfaces.styles import IStyleManager
from mailman.interfaces.usermanager import IUserManager
from mailman.utilities.modules import call_name
from public import public
from zope.component import getUtility


log = logging.getLogger('mailman.error')
# These are the only characters allowed in list names.  A more restrictive
# class can be specified in config.mailman.listname_chars.
_listname_chars = re.compile('[-_.+=!$*{}~0-9a-z]', re.IGNORECASE)


@public
def create_list(fqdn_listname, owners=None, style_name=None):
    """Create the named list and apply styles.

    The mailing may not exist yet, but the domain specified in `fqdn_listname`
    must exist.

    :param fqdn_listname: The fully qualified name for the new mailing list.
    :type fqdn_listname: string
    :param owners: The mailing list owners.
    :type owners: list of string email addresses
    :param style_name: The name of the style to apply to the newly created
        list.  If not given, the default is taken from the configuration file.
    :type style_name: string
    :return: The new mailing list.
    :rtype: `IMailingList`
    :raises BadDomainSpecificationError: when the hostname part of
        `fqdn_listname` does not exist.
    :raises ListAlreadyExistsError: when the mailing list already exists.
    :raises InvalidEmailAddressError: when the fqdn email address is invalid.
    :raises InvalidListNameError: when the fqdn email address is valid but the
        listname contains disallowed characters.
    """
    if owners is None:
        owners = []
    # This raises InvalidEmailAddressError if the address is not a valid
    # posting address.  Let these percolate up.
    getUtility(IEmailValidator).validate(fqdn_listname)
    listname, domain = fqdn_listname.split('@', 1)
    # We need to be fussier than just validating the posting address.  Various
    # legal local-part characters will cause problems in list names.
    # First we check our maximally allowed set.
    if len(_listname_chars.sub('', listname)) > 0:
        raise InvalidListNameError(listname)
    # Then if another set is configured, check that.
    if config.mailman.listname_chars:
        try:
            cre = re.compile(config.mailman.listname_chars, re.IGNORECASE)
        except re.error as error:
            log.error(
                'Bad config.mailman.listname_chars setting: %s: %s',
                config.mailman.listname_chars,
                getattr(error, 'msg', str(error))
                )
        else:
            if len(cre.sub('', listname)) > 0:
                raise InvalidListNameError(listname)
    if domain not in getUtility(IDomainManager):
        raise BadDomainSpecificationError(domain)
    mlist = getUtility(IListManager).create(fqdn_listname)
    style = getUtility(IStyleManager).get(
        config.styles.default if style_name is None else style_name)
    if style is not None:
        style.apply(mlist)
    # Coordinate with the MTA, as defined in the configuration file.
    call_name(config.mta.incoming).create(mlist)
    # Create any owners that don't yet exist, and subscribe all addresses as
    # owners of the mailing list.
    user_manager = getUtility(IUserManager)
    for owner_address in owners:
        address = user_manager.get_address(owner_address)
        if address is None:
            user = user_manager.create_user(owner_address)
            address = list(user.addresses)[0]
        mlist.subscribe(address, MemberRole.owner)
    return mlist


@public
def remove_list(mlist):
    """Remove the list and all associated artifacts and subscriptions."""
    # Remove the list's data directory, if it exists.
    with suppress(FileNotFoundError):
        shutil.rmtree(mlist.data_path)
    # Delete the mailing list from the database.
    getUtility(IListManager).delete(mlist)
    # Do the MTA-specific list deletion tasks
    call_name(config.mta.incoming).delete(mlist)
