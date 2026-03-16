# Copyright (C) 2026 FPLL Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""基本组合子 (combinators)  - 方便写一行 lambda 代码。"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

__all__ = ["I", "K", "S", "B", "C", "W", "Y", "Omega"]

# 组合子定义 (来自 Lambda 演算)

# I 组合子 (Identity): lambda x: x
def I(x: T) -> T:
    """Identity combinator: 返回输入本身。"""
    return x


# K 组合子 (Constant): lambda x: lambda y: x
def K(x: T) -> Callable[[Any], T]:
    """Constant combinator: 忽略第二个参数并返回第一个。"""

    def inner(_: Any) -> T:  # noqa: ARG001
        return x

    return inner


# S 组合子 (Substitution): lambda x: lambda y: lambda z: x(z)(y(z))
def S(x: Callable[[T], Callable[[U], V]]) -> Callable[[Callable[[T], U]], Callable[[T], V]]:
    """Substitution combinator: 等价于 function application in lambda calculus."""

    def outer(y: Callable[[T], U]) -> Callable[[T], V]:
        def inner(z: T) -> V:
            return x(z)(y(z))

        return inner

    return outer


# 常用的其他组合子

def B(f: Callable[[U], V]) -> Callable[[Callable[[T], U]], Callable[[T], V]]:
    """B 组合子 (黑鸟): 函数组合 (f . g)."""

    def inner(g: Callable[[T], U]) -> Callable[[T], V]:
        def call(x: T) -> V:
            return f(g(x))

        return call

    return inner


def C(f: Callable[[T, U], V]) -> Callable[[U, T], V]:
    """C 组合子 (交换参数顺序)."""

    def inner(y: U, x: T) -> V:
        return f(x, y)

    return inner


def W(f: Callable[[T], Callable[[T], U]]) -> Callable[[T], U]:
    """W 组合子（复制/双重应用）.

    W(f)(x) 等价于 f(x)(x)。
    """

    def inner(x: T) -> U:
        return f(x)(x)

    return inner


def Y(f: Callable[..., Any]) -> Any:
    """Y 组合子 (递归固定点)."""

    return (lambda x: f(lambda *a, **k: x(x)(*a, **k)))(
        lambda x: f(lambda *a, **k: x(x)(*a, **k))
    )


def Omega(f: Callable[..., Any]) -> Any:
    """Ω 组合子（非正规终止，用于演示无限递归）。"""

    return (lambda x: x(x))(lambda x: f(lambda *a, **k: x(x)(*a, **k)))
