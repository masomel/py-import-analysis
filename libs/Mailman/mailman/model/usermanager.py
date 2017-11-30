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

"""A user manager."""

from mailman.database.transaction import dbconnection
from mailman.interfaces.address import ExistingAddressError
from mailman.interfaces.usermanager import IUserManager
from mailman.model.address import Address
from mailman.model.autorespond import AutoResponseRecord
from mailman.model.digests import OneLastDigest
from mailman.model.member import Member
from mailman.model.preferences import Preferences
from mailman.model.user import User
from public import public
from zope.interface import implementer


@public
@implementer(IUserManager)
class UserManager:
    """See `IUserManager`."""

    def create_user(self, email=None, display_name=None):
        """See `IUserManager`."""
        if email:
            address = self.create_address(email, display_name)
        user = User(display_name, Preferences())
        if email:
            user.link(address)
        return user

    def make_user(self, email, display_name=None):
        """See `IUserManager`."""
        # See if there's already a user linked with the given address.
        user = self.get_user(email)
        if user is None:
            # A user linked to this address does not yet exist.  Is the
            # address itself known but just not linked to a user?
            address = self.get_address(email)
            if address is None:
                # Nope, we don't even know about this address, so create both
                # the user and address now.
                return self.create_user(email, display_name)
            # The address exists, but it's not yet linked to a user.  Create
            # the empty user object and link them together.
            user = self.create_user()
            user.display_name = (
                display_name if display_name else address.display_name)
            user.link(address)
        return user

    @dbconnection
    def delete_user(self, store, user):
        """See `IUserManager`."""
        # SQLAlchemy is susceptable to delete-elements-while-iterating bugs so
        # first figure out all the addresses we want to delete, then in a
        # separate pass, delete those addresses.  (See LP: #1419519)
        to_delete = list(user.addresses)
        for address in to_delete:
            self.delete_address(address)
        # Remove memberships.
        for membership in store.query(Member).filter_by(user_id=user.id):
            membership.unsubscribe()
        store.delete(user.preferences)
        store.delete(user)

    @dbconnection
    def get_user(self, store, email):
        """See `IUserManager`."""
        addresses = store.query(Address).filter_by(email=email.lower())
        if addresses.count() == 0:
            return None
        return addresses.one().user

    @dbconnection
    def get_user_by_id(self, store, user_id):
        """See `IUserManager`."""
        users = store.query(User).filter_by(_user_id=user_id)
        if users.count() == 0:
            return None
        return users.one()

    @property
    @dbconnection
    def users(self, store):
        """See `IUserManager`."""
        yield from store.query(User).order_by(User.id).all()

    @dbconnection
    def create_address(self, store, email, display_name=None):
        """See `IUserManager`."""
        addresses = store.query(Address).filter(Address.email == email.lower())
        if addresses.count() == 1:
            found = addresses[0]
            raise ExistingAddressError(found.original_email)
        assert addresses.count() == 0, 'Unexpected results'
        if display_name is None:
            display_name = ''
        # It's okay not to lower case the 'email' argument because the
        # constructor will do the right thing.
        address = Address(email, display_name)
        address.preferences = Preferences()
        store.add(address)
        return address

    @dbconnection
    def delete_address(self, store, address):
        """See `IUserManager`."""
        # If there's a user controlling this address, it has to first be
        # unlinked before the address can be deleted.
        if address.user:
            address.user.unlink(address)
        # Remove memberships.
        for membership in store.query(Member).filter_by(address_id=address.id):
            membership.unsubscribe()
        # Remove auto-response records.
        store.query(AutoResponseRecord).filter_by(address=address).delete()
        # Remove last digest record.
        store.query(OneLastDigest).filter_by(address=address).delete()
        # Now delete the address.
        store.delete(address)

    @dbconnection
    def get_address(self, store, email):
        """See `IUserManager`."""
        addresses = store.query(Address).filter_by(email=email.lower())
        if addresses.count() == 0:
            return None
        return addresses.one()

    @property
    @dbconnection
    def addresses(self, store):
        """See `IUserManager`."""
        yield from store.query(Address).all()

    @property
    @dbconnection
    def members(self, store):
        """See `IUserManager."""
        yield from store.query(Member).all()

    @property
    @dbconnection
    def server_owners(self, store):
        """ See `IUserManager."""
        yield from store.query(User).filter_by(is_server_owner=True)
