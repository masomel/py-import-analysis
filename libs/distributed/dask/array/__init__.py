from __future__ import absolute_import, division, print_function

from ..utils import ignoring
from .core import (Array, concatenate, stack, from_array, store, map_blocks,
                   atop, to_hdf5, to_npy_stack, from_npy_stack, from_delayed,
                   asarray, asanyarray, broadcast_to)
from .routines import (take, choose, argwhere, where, coarsen, insert,
                       ravel, roll, unique, squeeze, topk, diff, ediff1d,
                       bincount, digitize, histogram, cov, array, dstack,
                       vstack, hstack, compress, extract, round, count_nonzero,
                       flatnonzero, nonzero, around, isnull, notnull, isclose,
                       corrcoef, swapaxes, tensordot, transpose, dot,
                       result_type)
from .reshape import reshape
from .ufunc import (add, subtract, multiply, divide, logaddexp, logaddexp2,
        true_divide, floor_divide, negative, power, remainder, mod, conj, exp,
        exp2, log, log2, log10, log1p, expm1, sqrt, square, cbrt, reciprocal,
        sin, cos, tan, arcsin, arccos, arctan, arctan2, hypot, sinh, cosh,
        tanh, arcsinh, arccosh, arctanh, deg2rad, rad2deg, greater,
        greater_equal, less, less_equal, not_equal, equal, logical_and,
        logical_or, logical_xor, logical_not, maximum, minimum,
        fmax, fmin, isreal, iscomplex, isfinite, isinf, isnan, signbit,
        copysign, nextafter, spacing, ldexp, fmod, floor, ceil, trunc, degrees,
        radians, rint, fix, angle, real, imag, clip, fabs, sign, absolute,
        i0, sinc, nan_to_num, frexp, modf, divide)
from .reductions import (sum, prod, mean, std, var, any, all, min, max, vnorm,
                         moment,
                         argmin, argmax,
                         nansum, nanmean, nanstd, nanvar, nanmin,
                         nanmax, nanargmin, nanargmax,
                         cumsum, cumprod)
from .percentile import percentile
with ignoring(ImportError):
    from .reductions import nanprod, nancumprod, nancumsum
from . import random, linalg, ghost, learn, fft
from .wrap import ones, zeros, empty, full
from .rechunk import rechunk
from ..context import set_options
from ..base import compute
from .optimization import optimize
from .creation import (arange, linspace, indices, diag, eye, triu, tril,
                       fromfunction, tile, repeat)
