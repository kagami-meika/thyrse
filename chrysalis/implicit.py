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

"""隐式对象与链式 lambda 生成工具。

该模块提供一个魔法占位符 `_`，可以用于按链式方式构造 lambda 表达式。

示例:
    from fpll.implicit import _

    fn = _.upper() + "!"
    assert fn("hello") == "HELLO!"

该设计灵感来源于 Scala/Elixir 的隐式 lambda 语法。
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

import re

T = TypeVar("T")


class I:
    """隐式占位符。

    语义:
        - 作为函数使用时 (`fn(x)`), 会把 x 转给内部组合函数并返回结果。
        - 通过属性访问生成新的表达式（e.g. `_.upper`），属性会在最终调用时获取。
        - 通过调用带参数的属性访问生成方法调用表达式（e.g. `_.startswith("a")`）。

    该设计中，`method` 标志用于区分 "属性/方法构造" 模式与 "直接求值" 模式。
    当 `method=True` 时，调用 (`__call__`) 会把返回值当成可调用对象并执行它。
    """

    __slots__ = ("f", "method")

    def __init__(self, f: Callable[[Any], Any] = lambda x: x, method: bool = False):
        self.f = f
        self.method = method

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        # method 模式：当存在属性访问时，构造一个可组合的“方法调用”表达式。
        # 例如:
        #     _.upper()        -> lambda x: x.upper()
        #     _.replace("a", "b") -> lambda x: x.replace("a", "b")
        #
        # 在 method 模式下，__call__ 不会把传入的参数当作“待计算输入值”，而是当作方法调用的参数。
        if self.method:
            return I(lambda x: self.f(x)(*args, **kwargs), method=False)

        # 非 method 模式：如果传入恰好一个位置参数，则当作“求值”操作
        if len(args) == 1 and not kwargs:
            return self.f(args[0])

        # 其它调用（例如错误的使用方式）也当作求值处理，但会显式报错。
        raise TypeError(
            "Implicit placeholder can only be called for evaluation with a single argument (e.g. fn(x)), "
            "or used after attribute access to build a method call (e.g. _.upper() )."
        )

    def __getattr__(self, name: str) -> "I":
            if name.startswith("re_"):
                re_name = name[3:]
                try:
                    re_func = getattr(re, re_name)
                except AttributeError:
                    raise AttributeError(f"re module has no attribute '{re_name}'")
                
                def re_getter(x: Any) -> Callable[..., Any]:
                    def partial(*prefix: Any, **kw: Any) -> Any:
                        return re_func(*prefix, x, **kw)  # string 始终作为最后一个位置参数
                    return partial
                
                return I(re_getter, method=True)
            
            # 原有逻辑（保持不变）
            return I(lambda x: getattr(self.f(x), name), method=True)

    def __getitem__(self, key: Any) -> "I":
        # 支持 `_["key"]` / `_[0]` / `_[1:3]` 等索引 / 切片操作
        return I(lambda x: x[key])

    def __setitem__(self, key: Any, value: Any) -> "I":
        # 支持赋值操作（用于构造 lambda 中的赋值）
        return I(lambda x: (x.__setitem__(key, value), x)[1] if hasattr(x, '__setitem__') else x)

    def _binary_op(self, other: Any, op: Callable[[Any, Any], Any], reverse: bool = False) -> "I":
        if isinstance(other, I):
            if reverse:
                return I(lambda x: op(other.f(x), self.f(x)))
            return I(lambda x: op(self.f(x), other.f(x)))
        if reverse:
            return I(lambda x: op(other, self.f(x)))
        return I(lambda x: op(self.f(x), other))

    def __add__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a + b)

    def __radd__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a + b, reverse=True)

    def __sub__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a - b)

    def __rsub__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a - b, reverse=True)

    def __mul__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a * b)

    def __rmul__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a * b, reverse=True)

    def __truediv__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a / b)

    def __rtruediv__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a / b, reverse=True)

    def __floordiv__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a // b)

    def __rfloordiv__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a // b, reverse=True)

    def __mod__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a % b)

    def __rmod__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a % b, reverse=True)

    def __pow__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a**b)

    def __rpow__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a**b, reverse=True)

    # 逻辑运算（使用位运算符做组合）
    def __and__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a and b)

    def __or__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a or b)

    def __invert__(self) -> "I":
        return I(lambda x: not self.f(x))

    # 比较运算
    def __lt__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a < b)

    def __le__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a <= b)

    def __gt__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a > b)

    def __ge__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a >= b)

    def __eq__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a == b)

    def __ne__(self, other: Any) -> "I":
        return self._binary_op(other, lambda a, b: a != b)


def apply(func: Callable[..., T], *args: Any, **kwargs: Any) -> I | T:
    """使用 _ 占位符进行偏函数应用。

    这是一个包装函数，用于支持类似 `apply(sum, _, 1)` 等价于 `lambda x: sum(x, 1)` 的语法。

    示例:
        from fpll import apply, _

        sum_with_1 = apply(sum, _, 1)
        assert sum_with_1([1, 2, 3]) == 7  # sum([1,2,3], 1) = 7

        max_with_default = apply(max, _, default=0)
        assert max_with_default([1, 2, 3]) == 3

    参数:
        func: 要应用的函数
        *args: 位置参数，可以包含 _ 占位符
        **kwargs: 关键字参数

    返回值:
        如果包含 _ 占位符，返回一个 I 对象（即 lambda）
        否则直接调用 func 并返回结果

    抛出:
        ValueError: 如果使用了多个 _ 占位符或缺少 _ 占位符
    """
    # 找出所有占位符的位置
    placeholder_positions = [i for i, arg in enumerate(args) if isinstance(arg, I) and arg.f.__name__ == "<lambda>" and arg.f(None) is None]
    
    # 用更准确的方式检测是否是默认的 _ 占位符
    placeholder_positions = []
    for i, arg in enumerate(args):
        if isinstance(arg, I) and arg.method is False:
            # 检查这是否是默认的 _ 对象（通过比较 f 是否为恒等函数）
            try:
                if arg.f(42) == 42 and arg.f("test") == "test":
                    placeholder_positions.append(i)
            except:
                pass
    
    if not placeholder_positions:
        # 没有占位符，直接调用函数
        return func(*args, **kwargs)
    
    if len(placeholder_positions) > 1:
        raise ValueError(f"Cannot use multiple _ placeholders in apply. Found {len(placeholder_positions)} placeholders.")
    
    placeholder_pos = placeholder_positions[0]
    
    def bound_func(x: Any) -> T:
        # 将占位符替换为实际值
        new_args = [x if i == placeholder_pos else arg for i, arg in enumerate(args)]
        return func(*new_args, **kwargs)
    
    return I(bound_func)


# 约定：`_` 是隐式占位符，用于构造一行式表达式
_ = I()
