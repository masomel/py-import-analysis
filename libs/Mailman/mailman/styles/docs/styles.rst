.. _list-styles:

===========
List styles
===========

List styles are a way to name and apply a template of attribute settings to
new mailing lists.  Every style has a name, which must be unique.

Styles are generally only applied when a mailing list is created, although
there is no reason why styles can't be applied to an existing mailing list.
However, when a style changes, the mailing lists using that style are not
automatically updated.  Instead, think of styles as the initial set of
defaults for just about any mailing list attribute.  In fact, application of a
style to a mailing list can really modify the mailing list in any way.

To start with, there are a few legacy styles.

    >>> from zope.component import getUtility
    >>> from mailman.interfaces.styles import IStyleManager
    >>> manager = getUtility(IStyleManager)
    >>> for style in manager.styles:
    ...     print(style.name)
    legacy-announce
    legacy-default

When you create a mailing list through the low-level `IListManager` API, no
style is applied.

    >>> from mailman.interfaces.listmanager import IListManager
    >>> mlist = getUtility(IListManager).create('ant@example.com')
    >>> print(mlist.display_name)
    None

The legacy default style sets the list's display name.

    >>> manager.get('legacy-default').apply(mlist)
    >>> print(mlist.display_name)
    Ant


Registering styles
==================

New styles must implement the ``IStyle`` interface.

    >>> from zope.interface import implementer
    >>> from mailman.interfaces.styles import IStyle
    >>> @implementer(IStyle)
    ... class TestStyle:
    ...     name = 'a-test-style'
    ...     def apply(self, mailing_list):
    ...         # Just does something very simple.
    ...         mailing_list.display_name = 'TEST STYLE LIST'

You can register a new style with the style manager.

    >>> manager.register(TestStyle())

All registered styles are returned in alphabetical order by style name.

    >>> for style in manager.styles:
    ...     print(style.name)
    a-test-style
    legacy-announce
    legacy-default

You can also ask the style manager for the style, by name.

    >>> test_style = manager.get('a-test-style')
    >>> print(test_style.name)
    a-test-style


Unregistering styles
====================

You can unregister a style, making it unavailable in the future.

    >>> manager.unregister(test_style)
    >>> for style in manager.styles:
    ...     print(style.name)
    legacy-announce
    legacy-default

Asking for a missing style returns None.

    >>> print(manager.get('a-test-style'))
    None


.. _list-creation-styles:

Apply styles at list creation
=============================

You can specify a style to apply when creating a list through the high-level
API.  Let's start by registering the test style.

    >>> manager.register(test_style)

Now, when we use the high level API, we can ask for the style to be applied.

    >>> from mailman.app.lifecycle import create_list
    >>> mlist = create_list('bee@example.com', style_name=test_style.name)

The style has been applied.

    >>> print(mlist.display_name)
    TEST STYLE LIST

If no style name is provided when creating the list, the system default style
(taken from the configuration file) is applied.

    >>> @implementer(IStyle)
    ... class AnotherStyle:
    ...     name = 'another-style'
    ...     def apply(self, mailing_list):
    ...         # Just does something very simple.
    ...         mailing_list.display_name = 'ANOTHER STYLE LIST'
    >>> another_style = AnotherStyle()

We'll set up the system default to apply this newly registered style if no
other style is explicitly given.

    >>> from mailman.testing.helpers import configuration
    >>> with configuration('styles', default=another_style.name):
    ...     manager.register(another_style)
    ...     mlist = create_list('cat@example.com')
    >>> print(mlist.display_name)
    ANOTHER STYLE LIST
