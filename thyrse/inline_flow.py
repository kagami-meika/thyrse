"""控制流辅助工具。

Python 的 lambda 只能包含表达式，不支持语句形式的 if/else 或循环。
该模块提供内联三元表达式（iif）工具，以及函数式的“列表推导”写法。
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, TypeVar

T = TypeVar("T")
U = TypeVar("U")


def iif(cond: Any, t: Callable[[], T], f: Callable[[], T]) -> T:
    """内联三元表达式：根据条件执行 t() 或 f().

    Args:
        cond: 布尔值或可调用对象（如果是可调用对象则会调用得到结果）。
        t: 条件为真时调用的函数（延迟求值）。
        f: 条件为假时调用的函数（延迟求值）。

    示例:
        iif(x > 0, lambda: 1, lambda: -1)
    """

    value = cond() if callable(cond) else cond
    return t() if value else f()


def comprehension(
    fn: Callable[[T], U], iterable: Iterable[T], *preds: Callable[[T], bool]
) -> list[U]:
    """函数式列表推导：等价于 `[fn(x) for x in iterable if all(pred(x) for pred in preds)]`.

    这个函数可以作为“函数式的 list comprehension”替代。

    示例：
        comprehension(lambda x: x * 2, range(10), lambda x: x % 2 == 0)
    """

    if not preds:
        return [fn(x) for x in iterable]
    return [fn(x) for x in iterable if all(pred(x) for pred in preds)]
