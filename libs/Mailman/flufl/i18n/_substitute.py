"""Substitutions."""

import string

from public import public


_missing = object()


@public
class Template(string.Template):
    """Match any attribute path."""
    idpattern = r'[_a-z][_a-z0-9.]*'


@public
class attrdict(dict):
    """Follow attribute paths."""
    def __getitem__(self, key):
        parts = key.split('.')
        value = super().__getitem__(parts.pop(0))
        while parts:
            value = getattr(value, parts.pop(0), _missing)
            if value is _missing:
                raise KeyError(key)
        return value
