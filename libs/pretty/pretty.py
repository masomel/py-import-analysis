# -*- coding: utf-8 -*-
"""
    pretty
    ~~

    Python advanced pretty printer.  This pretty printer is intended to
    replace the old `pprint` python module which does not allow developers
    to provide their own pretty print callbacks.

    This module is based on ruby's `prettyprint.rb` library by `Tanaka Akira`.


    Example Usage
    =============

    To directly print the representation of an object use `pprint`::

        from pretty import pprint
        pprint(complex_object)

    To get a string of the output use `pretty`::

        from pretty import pretty
        string = pretty(complex_object)


    Extending
    =========

    The pretty library allows developers to add pretty printing rules for their
    own objects.  This process is straightforward.  All you have to do is to
    add a `__pretty__` method to your object and call the methods on the
    pretty printer passed::

        class MyObject(object):

            def __pretty__(self, p, cycle):
                ...

    Depending on the python version you want to support you have two
    possibilities.  The following list shows the python 2.5 version and the
    compatibility one.


    Here the example implementation of a `__pretty__` method for a list
    subclass for python 2.5 and higher (python 2.5 requires the with statement
    __future__ import)::

        class MyList(list):

            def __pretty__(self, p, cycle):
                if cycle:
                    p.text('MyList(...)')
                else:
                    with p.group(8, 'MyList([', '])'):
                        for idx, item in enumerate(self):
                            if idx:
                                p.text(',')
                                p.breakable()
                            p.pretty(item)

    The `cycle` parameter is `True` if pretty detected a cycle.  You *have* to
    react to that or the result is an infinite loop.  `p.text()` just adds
    non breaking text to the output, `p.breakable()` either adds a whitespace
    or breaks here.  If you pass it an argument it's used instead of the
    default space.  `p.pretty` prettyprints another object using the pretty print
    method.

    The first parameter to the `group` function specifies the extra indentation
    of the next line.  In this example the next item will either be not
    breaked (if the items are short enough) or aligned with the right edge of
    the opening bracked of `MyList`.

    If you want to support python 2.4 and lower you can use this code::

        class MyList(list):

            def __pretty__(self, p, cycle):
                if cycle:
                    p.text('MyList(...)')
                else:
                    p.begin_group(8, 'MyList([')
                    for idx, item in enumerate(self):
                        if idx:
                            p.text(',')
                            p.breakable()
                        p.pretty(item)
                    p.end_group(8, '])')

    If you just want to indent something you can use the group function
    without open / close parameters.  Under python 2.5 you can also use this
    code::

        with p.indent(2):
            ...

    Or under python2.4 you might want to modify ``p.indentation`` by hand but
    this is rather ugly.


    :copyright: 2007 by Armin Ronacher.
    :license: BSD License.
"""
import __future__
import sys
import types
import re
from StringIO import StringIO
from collections import deque


__all__ = ['pretty', 'pprint', 'PrettyPrinter', 'RepresentationPrinter']


_re_pattern_type = type(re.compile(''))


def pretty(obj, verbose=False, max_width=79, newline='\n'):
    """
    Pretty print the object's representation.
    """
    stream = StringIO()
    printer = RepresentationPrinter(stream, verbose, max_width, newline)
    printer.pretty(obj)
    printer.flush()
    return stream.getvalue()


def pprint(obj, verbose=False, max_width=79, newline='\n'):
    """
    Like `pretty` but print to stdout.
    """
    printer = RepresentationPrinter(sys.stdout, verbose, max_width, newline)
    printer.pretty(obj)
    printer.flush()
    sys.stdout.write(newline)
    sys.stdout.flush()


# add python2.5 context managers if we have the with statement feature
if hasattr(__future__, 'with_statement'): exec '''
from __future__ import with_statement
from contextlib import contextmanager

class _PrettyPrinterBase(object):

    @contextmanager
    def indent(self, indent):
        """with statement support for indenting/dedenting."""
        self.indentation += indent
        try:
            yield
        finally:
            self.indentation -= indent

    @contextmanager
    def group(self, indent=0, open='', close=''):
        """like begin_group / end_group but for the with statement."""
        self.begin_group(indent, open)
        try:
            with self.indent(indent):
                yield
        finally:
            self.end_group(indent, close)
'''
else:
    class _PrettyPrinterBase(object):

        def _unsupported(self, *a, **kw):
            """unsupported operation"""
            raise RuntimeError('not available in this python version')
        group = indent = _unsupported
        del _unsupported


class PrettyPrinter(_PrettyPrinterBase):
    """
    Baseclass for the `RepresentationPrinter` prettyprinter that is used to
    generate pretty reprs of objects.  Contrary to the `RepresentationPrinter`
    this printer knows nothing about the default pprinters or the `__pretty__`
    callback method.
    """

    def __init__(self, output, max_width=79, newline='\n'):
        self.output = output
        self.max_width = max_width
        self.newline = newline
        self.output_width = 0
        self.buffer_width = 0
        self.buffer = deque()

        root_group = Group(0)
        self.group_stack = [root_group]
        self.group_queue = GroupQueue(root_group)
        self.indentation = 0

    def _break_outer_groups(self):
        while self.max_width < self.output_width + self.buffer_width:
            group = self.group_queue.deq()
            if not group:
                return
            while group.breakables:
                x = self.buffer.popleft()
                self.output_width = x.output(self.output, self.output_width)
                self.buffer_width -= x.width
            while self.buffer and isinstance(self.buffer[0], Text):
                x = self.buffer.popleft()
                self.output_width = x.output(self.output, self.output_width)
                self.buffer_width -= x.width

    def text(self, obj):
        """Add literal text to the output."""
        width = len(obj)
        if self.buffer:
            text = self.buffer[-1]
            if not isinstance(text, Text):
                text = Text()
                self.buffer.append(text)
            text.add(obj, width)
            self.buffer_width += width
            self._break_outer_groups()
        else:
            self.output.write(obj)
            self.output_width += width

    def breakable(self, sep=' '):
        """
        Add a breakable separator to the output.  This does not mean that it
        will automatically break here.  If no breaking on this position takes
        place the `sep` is inserted which default to one space.
        """
        width = len(sep)
        group = self.group_stack[-1]
        if group.want_break:
            self.flush()
            self.output.write(self.newline)
            self.output.write(' ' * self.indentation)
            self.output_width = self.indentation
            self.buffer_width = 0
        else:
            self.buffer.append(Breakable(sep, width, self))
            self.buffer_width += width
            self._break_outer_groups()


    def begin_group(self, indent=0, open=''):
        """
        Begin a group.  If you want support for python < 2.5 which doesn't has
        the with statement this is the preferred way:

            p.begin_group(1, '{')
            ...
            p.end_group(1, '}')

        The python 2.5 expression would be this:

            with p.group(1, '{', '}'):
                ...

        The first parameter specifies the indentation for the next line (usually
        the width of the opening text), the second the opening text.  All
        parameters are optional.
        """
        if open:
            self.text(open)
        group = Group(self.group_stack[-1].depth + 1)
        self.group_stack.append(group)
        self.group_queue.enq(group)
        self.indentation += indent

    def end_group(self, dedent=0, close=''):
        """End a group. See `begin_group` for more details."""
        self.indentation -= dedent
        group = self.group_stack.pop()
        if not group.breakables:
            self.group_queue.remove(group)
        if close:
            self.text(close)

    def flush(self):
        """Flush data that is left in the buffer."""
        for data in self.buffer:
            self.output_width += data.output(self.output, self.output_width)
        self.buffer.clear()
        self.buffer_width = 0


class RepresentationPrinter(PrettyPrinter):
    """
    Special pretty printer that has a `pretty` method that calls the pretty
    printer for a python object.

    This class stores processing data on `self` so you must *never* use
    this class in a threaded environment.  Always lock it or reinstanciate
    it.

    Instances also have a verbose flag callbacks can access to control their
    output.  For example the default instance repr prints all attributes and
    methods that are not prefixed by an underscore if the printer is in
    verbose mode.
    """

    def __init__(self, output, verbose=False, max_width=79, newline='\n'):
        PrettyPrinter.__init__(self, output, max_width, newline)
        self.verbose = verbose
        self.stack = []

    def pretty(self, obj):
        """Pretty print the given object."""
        cycle = obj in self.stack
        self.stack.append(obj)
        self.begin_group()
        try:
            obj_class = getattr(obj, '__class__', None) or type(obj)
            if hasattr(obj_class, '__pretty__'):
                return obj_class.__pretty__(obj, self, cycle)
            try:
                printer = _singleton_pprinters[obj]
            except (TypeError, KeyError):
                pass
            else:
                return printer(obj, self, cycle)
            for cls in (obj_class,) + getattr(obj_class, '__bases__', ()):
                if cls in _type_pprinters:
                    return _type_pprinters[cls](obj, self, cycle)
            return _default_pprint(obj, self, cycle)
        finally:
            self.end_group()
            self.stack.pop()


class Printable(object):

    def output(self, stream, output_width):
        return output_width


class Text(Printable):

    def __init__(self):
        self.objs = []
        self.width = 0

    def output(self, stream, output_width):
        for obj in self.objs:
            stream.write(obj)
        return output_width + self.width

    def add(self, obj, width):
        self.objs.append(obj)
        self.width += width


class Breakable(Printable):

    def __init__(self, seq, width, pretty):
        self.obj = seq
        self.width = width
        self.pretty = pretty
        self.indentation = pretty.indentation
        self.group = pretty.group_stack[-1]
        self.group.breakables.append(self)

    def output(self, stream, output_width):
        self.group.breakables.popleft()
        if self.group.want_break:
            stream.write(self.pretty.newline)
            stream.write(' ' * self.indentation)
            return self.indentation
        if not self.group.breakables:
            self.pretty.group_queue.remove(self.group)
        stream.write(self.obj)
        return output_width + self.width


class Group(Printable):

    def __init__(self, depth):
        self.depth = depth
        self.breakables = deque()
        self.want_break = False


class GroupQueue(object):

    def __init__(self, *groups):
        self.queue = []
        for group in groups:
            self.enq(group)

    def enq(self, group):
        depth = group.depth
        while depth > len(self.queue) - 1:
            self.queue.append([])
        self.queue[depth].append(group)

    def deq(self):
        for stack in self.queue:
            for idx, group in enumerate(reversed(stack)):
                if group.breakables:
                    del stack[idx]
                    group.want_break = True
                    return group
            for group in stack:
                group.want_break = True
            del stack[:]

    def remove(self, group):
        try:
            self.queue[group.depth].remove(group)
        except ValueError:
            pass


def _default_pprint(obj, p, cycle):
    """
    The default print function.  Used if an object does not provide one and
    it's none of the builtin objects.
    """
    p.begin_group(1, '<')
    p.pretty(getattr(obj, '__class__', None) or type(obj))
    p.text(' at 0x%x' % (id(obj) & 0xffffffff))
    if cycle:
        p.text(' ...')
    elif p.verbose:
        first = True
        for key in dir(obj):
            if not key.startswith('_'):
                try:
                    value = getattr(obj, key)
                except AttributeError:
                    continue
                if isinstance(value, types.MethodType):
                    continue
                if not first:
                    p.text(',')
                p.breakable()
                p.text(key)
                p.text('=')
                step = len(key) + 1
                p.indentation += step
                p.pretty(value)
                p.indentation -= step
                first = False
    p.end_group(1, '>')


def _seq_pprinter_factory(start, end):
    """
    Factory that returns a pprint function useful for sequences.  Used by
    the default pprint for tuples, dicts, lists, sets and frozensets.
    """
    def inner(obj, p, cycle):
        if cycle:
            return p.text(start + '...' + end)
        step = len(start)
        p.begin_group(step, start)
        for idx, x in enumerate(obj):
            if idx:
                p.text(',')
                p.breakable()
            p.pretty(x)
        p.end_group(step, end)
    return inner


def _dict_pprinter_factory(start, end):
    """
    Factory that returns a pprint function used by the default pprint of
    dicts and dict proxies.
    """
    def inner(obj, p, cycle):
        if cycle:
            return p.text('{...}')
        p.begin_group(1, start)
        for idx, (key, value) in enumerate(obj.iteritems()):
            if idx:
                p.text(',')
                p.breakable()
            p.pretty(key)
            p.text(': ')
            p.pretty(value)
        p.end_group(1, end)
    return inner


def _super_pprint(obj, p, cycle):
    """The pprint for the super type."""
    p.begin_group(8, '<super: ')
    p.pretty(obj.__self_class__)
    p.text(',')
    p.breakable()
    p.pretty(obj.__self__)
    p.end_group(8, '>')


def _re_pattern_pprint(obj, p, cycle):
    """The pprint function for regular expression patterns."""
    p.text('re.compile(')
    pattern = repr(obj.pattern)
    if pattern[:1] in 'uU':
        pattern = pattern[1:]
        prefix = 'ur'
    else:
        prefix = 'r'
    pattern = prefix + pattern.replace('\\\\', '\\')
    p.text(pattern + ')')


def _type_pprint(obj, p, cycle):
    """The pprint for classes and types."""
    if obj.__module__ in ('__builtin__', 'exceptions'):
        name = obj.__name__
    else:
        name = obj.__module__ + '.' + obj.__name__
    p.text(name)


def _repr_pprint(obj, p, cycle):
    """A pprint that just redirects to the normal repr function."""
    p.text(repr(obj))


def _function_pprint(obj, p, cycle):
    """Base pprint for all functions and builtin functions."""
    if obj.__module__ in ('__builtin__', 'exceptions') or not obj.__module__:
        name = obj.__name__
    else:
        name = obj.__module__ + '.' + obj.__name__
    p.text('<function %s>' % name)


def _exception_pprint(obj, p, cycle):
    """Base pprint for all exceptions."""
    if obj.__class__.__module__ == 'exceptions':
        name = obj.__class__.__name__
    else:
        name = '%s.%s' % (
            obj.__class__.__module__,
            obj.__class__.__name__
        )
    step = len(name) + 1
    p.begin_group(step, '(')
    for idx, arg in enumerate(getattr(obj, 'args', ())):
        if idx:
            p.text(',')
            p.breakable()
        p.pretty(arg)
    p.end_group(step, ')')


#: the exception base
try:
    _exception_base = BaseException
except NameError:
    _exception_base = Exception


#: printers for builtin types
_type_pprinters = {
    int:                        _repr_pprint,
    long:                       _repr_pprint,
    float:                      _repr_pprint,
    str:                        _repr_pprint,
    unicode:                    _repr_pprint,
    tuple:                      _seq_pprinter_factory('(', ')'),
    list:                       _seq_pprinter_factory('[', ']'),
    dict:                       _dict_pprinter_factory('{', '}'),
    types.DictProxyType:        _dict_pprinter_factory('<dictproxy {', '}>'),
    set:                        _seq_pprinter_factory('set([', '])'),
    frozenset:                  _seq_pprinter_factory('frozenset([', '])'),
    super:                      _super_pprint,
    _re_pattern_type:           _re_pattern_pprint,
    type:                       _type_pprint,
    types.ClassType:            _type_pprint,
    types.FunctionType:         _function_pprint,
    types.BuiltinFunctionType:  _function_pprint,
    types.SliceType:            _repr_pprint,
    types.MethodType:           _repr_pprint,
    xrange:                     _repr_pprint,
    _exception_base:            _exception_pprint
}


#: printers for the default singletons
_singleton_pprinters = dict.fromkeys([None, True, False, Ellipsis,
                                      NotImplemented], _repr_pprint)


#: get rid of the unused things
del _PrettyPrinterBase, _repr_pprint, _seq_pprinter_factory, \
    _dict_pprinter_factory, _super_pprint, _re_pattern_pprint, \
    _type_pprint, _function_pprint, _exception_pprint, _exception_base


if __name__ == '__main__':
    from random import randrange
    class Foo(object):
        def __init__(self):
            self.foo = 1
            self.bar = re.compile(r'\s+')
            self.blub = dict.fromkeys(range(30), randrange(1, 40))
            self.hehe = 23424.234234
            self.list = ["blub", "blah", self]

        def get_foo(self):
            print "foo"

    pprint(Foo(), verbose=True)
