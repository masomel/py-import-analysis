=======
Domains
=======

..  # The test framework starts out with an example domain, so let's delete
    # that first.
    >>> from mailman.interfaces.domain import IDomainManager
    >>> from zope.component import getUtility
    >>> manager = getUtility(IDomainManager)
    >>> manager.remove('example.com')
    <Domain example.com...>

Domains are how Mailman interacts with email host names and web host names.
::

    >>> from operator import attrgetter
    >>> def show_domains(*, with_owners=False):
    ...     if len(manager) == 0:
    ...         print('no domains')
    ...         return
    ...     for domain in sorted(manager, key=attrgetter('mail_host')):
    ...         print(domain)
    ...     owners = sorted(owner.addresses[0].email
    ...                     for owner in domain.owners)
    ...     for owner in owners:
    ...         print('- owner:', owner)

    >>> show_domains()
    no domains

Adding a domain requires some basic information, of which the email host name
is the only required piece.  The other parts are inferred from that.

    >>> manager.add('example.org')
    <Domain example.org>
    >>> show_domains()
    <Domain example.org>

We can remove domains too.

    >>> manager.remove('example.org')
    <Domain example.org>
    >>> show_domains()
    no domains

Sometimes the email host name is different than the base url for hitting the
web interface for the domain.

    >>> manager.add('example.com')
    <Domain example.com>
    >>> show_domains()
    <Domain example.com>

Domains can have explicit descriptions, and can be created with one or more
owners.
::

    >>> manager.add(
    ...     'example.net',
    ...     description='The example domain',
    ...     owners=['anne@example.com'])
    <Domain example.net, The example domain>

    >>> show_domains(with_owners=True)
    <Domain example.com>
    <Domain example.net, The example domain>
    - owner: anne@example.com

Domains can have multiple owners, ideally one of the owners should have a
verified preferred address.  However this is not checked right now and the
configuration's default contact address may be used as a fallback.

   >>> net_domain = manager['example.net']
   >>> net_domain.add_owner('bart@example.org')
   >>> show_domains(with_owners=True)
   <Domain example.com>
   <Domain example.net, The example domain>
   - owner: anne@example.com
   - owner: bart@example.org

Domains can list all associated mailing lists with the mailing_lists property.
::

    >>> def show_lists(domain):
    ...     mlists = list(domain.mailing_lists)
    ...     for mlist in mlists:
    ...         print(mlist)
    ...     if len(mlists) == 0:
    ...         print('no lists')

    >>> net_domain = manager['example.net']
    >>> com_domain = manager['example.com']
    >>> show_lists(net_domain)
    no lists

    >>> create_list('test@example.net')
    <mailing list "test@example.net" at ...>
    >>> transaction.commit()
    >>> show_lists(net_domain)
    <mailing list "test@example.net" at ...>

    >>> show_lists(com_domain)
    no lists

In the global domain manager, domains are indexed by their email host name.
::

    >>> for domain in sorted(manager, key=attrgetter('mail_host')):
    ...     print(domain.mail_host)
    example.com
    example.net

    >>> print(manager['example.net'])
    <Domain example.net, The example domain>

As with dictionaries, you can also get the domain.  If the domain does not
exist, ``None`` or a default is returned.
::

    >>> print(manager.get('example.net'))
    <Domain example.net, The example domain>

    >>> print(manager.get('doesnotexist.com'))
    None

    >>> print(manager.get('doesnotexist.com', 'blahdeblah'))
    blahdeblah
