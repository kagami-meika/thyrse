# This software is in the public domain. 
# CC0 1.0 Universal - No rights reserved.
# To the extent possible under law, the person who associated CC0 
# with this work has waived all copyright and related or neighboring rights 
# to this work.
#
# See: http://creativecommons.org/publicdomain/zero/1.0/

"""Thyrse - A fast and elegant functional programming toolkit for Python

A comprehensive toolkit for functional programming, providing lambda calculus 
combinators, higher-order functions, algebraic data types, lenses, and more.

Quick start:
    from thyrse import I, K, S, curry, tap, pipe, Some, Ok

    # Combinators
    assert I(1) == 1
    assert K(1)(2) == 1

    # Function utilities
    add = curry(lambda x, y: x + y)
    add_five = add(5)
    assert add_five(3) == 8

    # Pipeline operations
    result = pipe(
        [1, 2, 3],
        lambda x: map(lambda i: i * 2, x),
        list,
    )
    assert result == [2, 4, 6]

    # Algebraic data types
    some_value = Some(5)
    assert some_value.map(lambda x: x * 2).get_or_else(0) == 10
"""

from .combinators import I, K, S, B, C, W, Y, Omega
from .func import (
    curry,
    compose,
    pipe,
    tap,
    always,
    flip,
    complement,
    retry,
    memoize,
    log,
    partition,
    groupby,
    async_compose,
    async_pipe,
    async_groupby,
    async_partition,
    fork,
    uncurry,
    branch,
    trace_pipeline,
    peek,
)
from .predicates import get_in, prop, get, has, is_type, and_, or_, not_, truthy, falsy
from .lazy import thunk, force, Lazy, AsyncLazy
from .implicit import _, I as Implicit, apply,MultiI, ImplicitSeries,ims, _0, _1, _2, _3, _4, _5, _6, _7, _8, _9, _a, _b, _c, _d, _e, _f
from .inline_flow import iif, comprehension
from .declarative_flow import attempt, using, match
from .adts import Optional, Some, Nothing, Result, Ok, Err, AsyncResult, AsyncOk, AsyncErr
from .lens import lens, lens_path, path, lens_key, lens_index, lens_attr, view, set_, over
from .safe import Safe, safe

__all__ = [
    "I",
    "Implicit",
    "_",
    "apply",
    "K",
    "S",
    "B",
    "C",
    "W",
    "Y",
    "Omega",
    "curry",
    "compose",
    "pipe",
    "tap",
    "always",
    "flip",
    "complement",
    "retry",
    "memoize",
    "log",
    "partition",
    "groupby",
    "async_compose",
    "async_pipe",
    "async_groupby",
    "async_partition",
    "fork",
    "uncurry",
    "branch",
    "prop",
    "get",
    "get_in",
    "has",
    "is_type",
    "and_",
    "or_",
    "not_",
    "truthy",
    "falsy",
    "thunk",
    "force",
    "Lazy",
    "AsyncLazy",
    "iif",
    "comprehension",
    "Safe",
    "safe",
    "attempt",
    "using",
    "match",
    "Optional",
    "Some",
    "Nothing",
    "Result",
    "Ok",
    "Err",
    "AsyncResult",
    "AsyncOk",
    "AsyncErr",
    "lens",
    "lens_path",
    "path",
    "lens_key",
    "lens_index",
    "lens_attr",
    "view",
    "set_",
    "over",
    "trace_pipeline",
    "peek",
    "ims",
    "_0", "_1", "_2", "_3", "_4", "_5", "_6", "_7", "_8", "_9",
    "_a", "_b", "_c", "_d", "_e", "_f",
    "MultiI",
    "ImplicitSeries",
]
