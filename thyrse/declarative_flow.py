"""声明式控制流工具。

提供函数化的异常处理、上下文管理器、模式匹配等。
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Dict, Type, TypeVar

T = TypeVar("T")
U = TypeVar("U")


def attempt(fn: Callable[[], T], catch: Type[Exception] | tuple[Type[Exception], ...], fallback: U) -> T | U:
    """函数化异常处理：尝试执行 fn，如果抛出指定异常则返回 fallback。

    示例:
        result = attempt(lambda: 1 / 0, catch=ZeroDivisionError, fallback=0)
    """

    try:
        return fn()
    except catch:
        return fallback


def using(resource: Any, fn: Callable[[Any], T]) -> T:
    """内联上下文管理器：使用资源执行 fn，自动处理 __enter__/__exit__。

    示例:
        result = using(open("test.txt"), lambda f: f.read())
    """

    with resource as r:
        return fn(r)


def match(value: Any, cases: Dict[Callable[[Any], bool], Any], default: Any = None) -> Any:
    """基于谓词的模式匹配：按顺序检查谓词，返回第一个匹配的值。

    示例:
        result = match(x, {lambda v: v > 0: "Pos", lambda v: v < 0: "Neg"}, default="Zero")
    """

    for pred, result in cases.items():
        if pred(value):
            return result
    return default
