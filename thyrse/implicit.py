"""隐式对象与链式 lambda 生成工具。

该模块提供一个魔法占位符 `_`，可以用于按链式方式构造 lambda 表达式。

示例:
    from .implicit import _

    fn = _.upper() + "!"
    assert fn("hello") == "HELLO!"

该设计灵感来源于 Scala/Elixir 的隐式 lambda 语法。
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar, Tuple

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


# --- 新增 MultiI 类 (继承 I，处理多变量) ---
class MultiI(I):
    """多变量隐式占位符。其内部 f 接受整个参数元组。"""
    __slots__ = ("f", "method")

    def __init__(self, f: Callable[[Tuple[Any, ...]], Any], method: bool = False):
        super().__init__(f, method)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self.method:
            return MultiI(lambda a: self.f(a)(*args, **kwargs), method=False)
        # 多变量版本直接消费所有 args
        return self.f(args)

    def __getattr__(self, name: str) -> MultiI:
        return MultiI(lambda a: getattr(self.f(a), name), method=True)

    def __getitem__(self, key: Any) -> MultiI:
        return MultiI(lambda a: self.f(a)[key])

    # 运算符重载，始终返回 MultiI
    def _binary_op(self, other: Any, op: Callable[[Any, Any], Any], reverse: bool = False) -> "MultiI":
        if isinstance(other, MultiI):
            if reverse:
                return MultiI(lambda x: op(other.f(x), self.f(x)))
            return MultiI(lambda x: op(self.f(x), other.f(x)))
        if isinstance(other, I):
            if reverse:
                return MultiI(lambda x: op(other.f(x), self.f(x)))
            return MultiI(lambda x: op(self.f(x), other.f(x)))
        if reverse:
            return MultiI(lambda x: op(other, self.f(x)))
        return MultiI(lambda x: op(self.f(x), other))

    def __add__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a + b)

    def __radd__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a + b, reverse=True)

    def __sub__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a - b)

    def __rsub__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a - b, reverse=True)

    def __mul__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a * b)

    def __rmul__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a * b, reverse=True)

    def __truediv__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a / b)

    def __rtruediv__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a / b, reverse=True)

    def __floordiv__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a // b)

    def __rfloordiv__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a // b, reverse=True)

    def __mod__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a % b)

    def __rmod__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a % b, reverse=True)

    def __pow__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a**b)

    def __rpow__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a**b, reverse=True)

    # 逻辑运算
    def __and__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a and b)

    def __or__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a or b)

    def __invert__(self) -> "MultiI":
        return MultiI(lambda x: not self.f(x))

    # 比较运算
    def __lt__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a < b)

    def __le__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a <= b)

    def __gt__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a > b)

    def __ge__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a >= b)

    def __eq__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a == b)

    def __ne__(self, other: Any) -> "MultiI":
        return self._binary_op(other, lambda a, b: a != b)

class ImplicitSeries:
    """提供 _0, _1 ... _f 的无限迭代器。"""
    def __init__(self):
        self._cache = {}

    def __getitem__(self, index: int) -> MultiI:
        if index not in self._cache:
            # 核心逻辑：从参数元组中提取特定索引的值
            self._cache[index] = MultiI(f=lambda args, i=index: args[i])
        return self._cache[index]

    def __getattr__(self, name: str) -> MultiI:
        if name.startswith("_"):
            try:
                return self[int(name[1:], 16)]
            except ValueError:
                raise AttributeError(name)
        raise AttributeError(name)

# --- 增强的 apply 函数 ---
def apply(func: Callable[..., T], *args: Any, **kwargs: Any) -> I | MultiI | T:
    """支持 I (_) 和 MultiI (_n) 的偏函数应用。"""
    # 查找所有占位符及其类型
    placeholders = []
    for i, arg in enumerate(args):
        if isinstance(arg, MultiI):
            placeholders.append((i, "multi"))
        elif isinstance(arg, I):
            # 检查是否是原始的单变量 _ (恒等函数)
            placeholders.append((i, "single"))

    if not placeholders:
        return func(*args, **kwargs)

    # 如果有多个占位符，统一升级为 MultiI 逻辑
    def bound_func(input_args: Tuple[Any, ...]) -> T:
        new_args = list(args)
        multi_idx = 0
        for pos, p_type in placeholders:
            if p_type == "multi":
                # MultiI 占位符自带取值逻辑
                new_args[pos] = args[pos].f(input_args)
            else:
                # 单变量 _ 默认按顺序消耗传入的参数
                new_args[pos] = input_args[multi_idx]
                multi_idx += 1
        return func(*new_args, **kwargs)

    return MultiI(bound_func)


# 约定：`_` 是隐式占位符，用于构造一行式表达式
_ = I()
ims = ImplicitSeries()
_0, _1, _2, _3, _4, _5, _6, _7, _8, _9 = (ims[i] for i in range(10))
_a, _b, _c, _d, _e, _f = (ims[i] for i in range(10, 16))