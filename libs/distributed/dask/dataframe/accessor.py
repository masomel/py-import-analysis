from __future__ import absolute_import, division, print_function

import numpy as np
import pandas as pd
from toolz import partial

from ..utils import derived_from


def maybe_wrap_pandas(obj, x):
    if isinstance(x, np.ndarray):
        if isinstance(obj, pd.Series):
            return pd.Series(x, index=obj.index, dtype=x.dtype)
        return pd.Index(x)
    return x


class Accessor(object):
    """
    Base class for pandas Accessor objects cat, dt, and str.

    Notes
    -----
    Subclasses should define the following attributes:

    * _accessor
    * _accessor_name
    """
    _not_implemented = set()

    def __init__(self, series):
        from .core import Series
        if not isinstance(series, Series):
            raise ValueError('Accessor cannot be initialized')
        self._validate(series)
        self._series = series

    def _validate(self, series):
        pass

    @staticmethod
    def _delegate_property(obj, accessor, attr):
        out = getattr(getattr(obj, accessor, obj), attr)
        return maybe_wrap_pandas(obj, out)

    @staticmethod
    def _delegate_method(obj, accessor, attr, args, kwargs):
        out = getattr(getattr(obj, accessor, obj), attr)(*args, **kwargs)
        return maybe_wrap_pandas(obj, out)

    def _property_map(self, attr):
        meta = self._delegate_property(self._series._meta,
                                       self._accessor_name, attr)
        token = '%s-%s' % (self._accessor_name, attr)
        return self._series.map_partitions(self._delegate_property,
                                           self._accessor_name, attr,
                                           token=token, meta=meta)

    def _function_map(self, attr, *args, **kwargs):
        meta = self._delegate_method(self._series._meta_nonempty,
                                     self._accessor_name,  attr, args, kwargs)
        token = '%s-%s' % (self._accessor_name, attr)
        return self._series.map_partitions(self._delegate_method,
                                           self._accessor_name, attr, args,
                                           kwargs, meta=meta, token=token)

    @property
    def _delegates(self):
        return set(dir(self._accessor)).difference(self._not_implemented)

    def __dir__(self):
        o = self._delegates
        o.update(self.__dict__)
        o.update(dir(type(self)))
        return list(o)

    def __getattr__(self, key):
        if key in self._delegates:
            if isinstance(getattr(self._accessor, key), property):
                return self._property_map(key)
            else:
                return partial(self._function_map, key)
        else:
            raise AttributeError(key)


class DatetimeAccessor(Accessor):
    """ Accessor object for datetimelike properties of the Series values.

    Examples
    --------

    >>> s.dt.microsecond  # doctest: +SKIP
    """
    _accessor = pd.Series.dt
    _accessor_name = 'dt'


class StringAccessor(Accessor):
    """ Accessor object for string properties of the Series values.

    Examples
    --------

    >>> s.str.lower()  # doctest: +SKIP
    """
    _accessor = pd.Series.str
    _accessor_name = 'str'
    _not_implemented = {'get_dummies'}

    def _validate(self, series):
        if not series.dtype == 'object':
            raise AttributeError("Can only use .str accessor with object dtype")

    @derived_from(pd.core.strings.StringMethods)
    def split(self, pat=None, n=-1):
        return self._function_map('split', pat=pat, n=n)
