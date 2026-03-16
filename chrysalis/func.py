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

"""函数式工具: 柯里化、组合、管道、调试 Tap 等。"""

from __future__ import annotations

import asyncio
import functools
import inspect
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Awaitable, Callable, Dict, Iterable, Tuple, TypeVar

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

__all__ = [
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
    "trace_pipeline",
    "peek",
]


# def curry(func: Callable[..., U]) -> Callable[..., Any]:
#     """将函数转为柯里化形式。

#     柯里化版本会一直返回一个可调用对象，直到提供了足够的参数调用原始函数。
#     支持位置参数、关键字参数、默认值，以及可变参数（*args/**kwargs）。

#     例: @curry
#         def add(x, y): return x + y

#     则可以写成: add(1)(2)
#     """

#     sig = inspect.signature(func)

#     total_params = [
#         p
#         for p in sig.parameters.values()
#         if p.kind
#         in (
#             inspect.Parameter.POSITIONAL_ONLY,
#             inspect.Parameter.POSITIONAL_OR_KEYWORD,
#             inspect.Parameter.KEYWORD_ONLY,
#         )
#     ]
#     expected_arg_count = len(total_params)

#     def _make_curried(*acc_args: Any, **acc_kwargs: Any) -> Callable[..., Any]:
#         @functools.wraps(func)
#         def _inner(*args: Any, **kwargs: Any) -> Any:
#             merged_args = (*acc_args, *args)
#             merged_kwargs = {**acc_kwargs, **kwargs}

#             bound = sig.bind_partial(*merged_args, **merged_kwargs)
#             bound_args_count = len(bound.arguments)

#             # If user explicitly calls with no new args, evaluate using defaults.
#             if not args and not kwargs:
#                 return func(*merged_args, **merged_kwargs)

#             if bound_args_count >= expected_arg_count:
#                 return func(*merged_args, **merged_kwargs)

#             return _make_curried(*merged_args, **merged_kwargs)

#         return _inner

#     return _make_curried()

def curry(func: Callable[..., U]) -> Callable[..., Any]:
    """
    将函数转为柯里化形式。

    行为规则：
    1. 固定参数函数（无 *args/**kwargs）：参数足够时自动求值（与原来一致）
    2. 可变参数函数（有 *args 或 **kwargs）：需要显式空调用 () 才能触发最终执行
    3. 支持默认值、关键字参数、位置参数混合使用

    示例：
        @curry
        def add(x, y): return x + y
        add(1)(2)             # → 3

        @curry
        def pipe(*fs): ...    # 可变参数
        pipe(f1)(f2)(f3)()    # 需要 () 结束收集
    """
    sig = inspect.signature(func)

    # 是否存在可变位置参数或可变关键字参数
    has_var_pos = any(
        p.kind == inspect.Parameter.VAR_POSITIONAL
        for p in sig.parameters.values()
    )
    has_var_kw = any(
        p.kind == inspect.Parameter.VAR_KEYWORD
        for p in sig.parameters.values()
    )
    is_vararg_func = has_var_pos or has_var_kw

    # 统计“必须提供的”位置/关键字参数数量（不含 *args/**kwargs 和默认值已满足的）
    required_params = [
        p for p in sig.parameters.values()
        if p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ) and p.default is inspect.Parameter.empty
    ]
    min_required_count = len(required_params)

    # 所有非 var 的参数（用于判断是否达到“饱和”）
    fixed_params = [
        p for p in sig.parameters.values()
        if p.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    ]
    expected_fixed_count = len(fixed_params)

    def _make_curried(*acc_args: Any, **acc_kwargs: Any) -> Callable[..., Any]:
        @functools.wraps(func)
        def _inner(*args: Any, **kwargs: Any) -> Any:
            merged_args = (*acc_args, *args)
            merged_kwargs = {**acc_kwargs, **kwargs}

            # 尝试绑定已有的参数（用于计数和检查）
            try:
                bound = sig.bind_partial(*merged_args, **merged_kwargs)
                bound_args_count = len(bound.arguments)
            except TypeError:
                # 参数冲突或非法调用，交给最终执行时抛出
                bound_args_count = 0

            # 情况1：用户显式空调用 () → 强制求值（最优先）
            if not args and not kwargs:
                return func(*merged_args, **merged_kwargs)

            # 情况2：固定参数函数，且参数已经足够 → 自动求值
            if not is_vararg_func and bound_args_count >= expected_fixed_count:
                return func(*merged_args, **merged_kwargs)

            # 情况3：可变参数函数，或固定参数尚未饱和 → 继续柯里化
            return _make_curried(*merged_args, **merged_kwargs)

        return _inner

    return _make_curried()


def compose(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    """函数组合: compose(f, g, h)(x) == f(g(h(x)))"""

    if not funcs:
        return lambda x: x

    def _composed(*args: Any, **kwargs: Any) -> Any:
        value = funcs[-1](*args, **kwargs)
        for f in reversed(funcs[:-1]):
            value = f(value)
        return value

    return _composed


def pipe(*funcs: Callable[..., Any]) -> Callable[..., Any]:
    """类似于管道: pipe(f, g, h)(x) == h(g(f(x)))"""

    return compose(*reversed(funcs))


def tap(fn: Callable[[T], Any]) -> Callable[[T], T]:
    """在链中插入副作用而不改变值。

    例:
        (tap(print)(x), x)[1]
        # 或者在管道中: pipe(..., tap(print), ...)
    """

    def _inner(value: T) -> T:
        fn(value)
        return value

    return _inner


def always(value: T) -> Callable[..., T]:
    """总是返回同一个值的函数 (类似 K 组合子)。"""

    def _inner(*_: Any, **__: Any) -> T:  # noqa: ARG002
        return value

    return _inner


def flip(func: Callable[..., Any]) -> Callable[..., Any]:
    """翻转函数的前两个参数。"""

    def _flipped(a: Any, b: Any, *args: Any, **kwargs: Any) -> Any:
        return func(b, a, *args, **kwargs)

    return _flipped


def complement(func: Callable[..., bool]) -> Callable[..., bool]:
    """逻辑取反的谓词。"""

    def _inner(*args: Any, **kwargs: Any) -> bool:
        return not func(*args, **kwargs)

    return _inner


def retry(times: int):
    """返回一个 decorator，用于在异常时重试函数。

    示例:
        @retry(3)
        def unstable():
            ...
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        def _wrapped(*args: Any, **kwargs: Any) -> T:
            last_err = None
            for _ in range(times):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_err = e
            raise last_err

        return _wrapped

    return decorator


def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """简单记忆化 (memoization) 装饰器。"""

    cache: Dict[Tuple[Any, ...], T] = {}

    def _wrapped(*args: Any, **kwargs: Any) -> T:
        key = (args, tuple(sorted(kwargs.items())))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return _wrapped


def log(prefix: str = "") -> Callable[[T], T]:
    """类似 tap，但打印带前缀的值。"""

    def _inner(value: T) -> T:
        print(f"{prefix}{value}")
        return value

    return _inner


def partition(pred: Callable[[T], bool], coll: Iterable[T]) -> Tuple[list[T], list[T]]:
    """将集合按 predicate 分为 (满足, 不满足) 两部分。"""

    trues: list[T] = []
    falses: list[T] = []
    for x in coll:
        (trues if pred(x) else falses).append(x)
    return trues, falses


def groupby(key_fn: Callable[[T], U], coll: Iterable[T]) -> Dict[U, list[T]]:
    """按 key_fn 分组，返回 key -> list(value) 的字典。"""

    out: Dict[U, list[T]] = {}
    for x in coll:
        k = key_fn(x)
        out.setdefault(k, []).append(x)
    return out


async def async_compose(*funcs: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """异步函数组合: async_compose(f, g, h)(x) == await f(await g(await h(x)))"""

    if not funcs:
        return lambda x: x

    async def _composed(*args: Any, **kwargs: Any) -> Any:
        value = await funcs[-1](*args, **kwargs)
        for f in reversed(funcs[:-1]):
            value = await f(value)
        return value

    return _composed


async def async_pipe(*funcs: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """异步管道: async_pipe(f, g, h)(x) == await h(await g(await f(x)))"""

    return await async_compose(*reversed(funcs))


async def async_groupby(key_fn: Callable[[T], U], coll: Iterable[T], max_workers: int = 4) -> Dict[U, list[T]]:
    """异步分组：使用多线程并行计算 key_fn，避免阻塞。"""

    async def _compute_key(x: T) -> Tuple[U, T]:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            k = await loop.run_in_executor(executor, key_fn, x)
        return k, x

    tasks = [_compute_key(x) for x in coll]
    results = await asyncio.gather(*tasks)

    out: Dict[U, list[T]] = {}
    for k, x in results:
        out.setdefault(k, []).append(x)
    return out


async def async_partition(pred: Callable[[T], bool], coll: Iterable[T], max_workers: int = 4) -> Tuple[list[T], list[T]]:
    """异步分区：并行评估谓词。"""

    async def _check_pred(x: T) -> Tuple[bool, T]:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            res = await loop.run_in_executor(executor, pred, x)
        return res, x

    tasks = [_check_pred(x) for x in coll]
    results = await asyncio.gather(*tasks)

    trues: list[T] = []
    falses: list[T] = []
    for pred_result, x in results:
        (trues if pred_result else falses).append(x)
    return trues, falses


class PipelineDebugger:
    """调试管道：记录每一步的输入输出。"""

    def __init__(self, initial_value: Any):
        self.steps: list[tuple[str, Any, Any]] = []
        self.current = initial_value

    def __rshift__(self, fn: Callable[[Any], Any]) -> "PipelineDebugger":
        result = fn(self.current)
        self.steps.append((fn.__name__ if hasattr(fn, '__name__') else str(fn), self.current, result))
        self.current = result
        return self

    def trace(self) -> list[tuple[str, Any, Any]]:
        return self.steps

    def value(self) -> Any:
        return self.current


def peek(label: str = "", condition: Callable[[Any], bool] = lambda x: True) -> Callable[[T], T]:
    """Peek 算子：条件打印中间值。"""

    def _inner(value: T) -> T:
        if condition(value):
            print(f"{label}{value}")
        return value

    return _inner


def trace_pipeline(initial: Any) -> PipelineDebugger:
    """创建可跟踪的管道。"""

    return PipelineDebugger(initial)


def fork(*funcs: Callable[..., Any]) -> Callable[[Any], Tuple[Any, ...]]:
    """并行分发：将单一输入应用到多个函数，返回结果元组。

    fork 实现数据的并行分发，将一个输入分别传递给多个函数，
    并将所有结果打包成元组。这在构建复杂计算图时很有用。

    示例:
        a = lambda x: x + 1
        b = lambda x: x * 2
        f = fork(a, b)
        f(5)  # → (6, 10)

    等价于:
        lambda x: (a(x), b(x))
    """

    def forked(value: Any) -> Tuple[Any, ...]:
        return tuple(func(value) for func in funcs)

    return forked


def uncurry(func: Callable[..., T]) -> Callable[[Tuple[Any, ...] | Any], T]:
    """反柯里化：将接收多个位置参数的函数转换为接收元组/序列的函数。

    uncurry 用于将元组解包后调用原函数，这对适配 pipe 的单一输入流很有用。
    特别是在 branch 函数内部，用于合并多个分支的结果。

    示例:
        def add(x, y):
            return x + y

        add_uncurried = uncurry(add)
        add_uncurried((2, 3))  # → 5

    如果传入的不是元组，会直接传给原函数（用于单参数情况）:
        single_arg_func = lambda x: x * 2
        uncurry(single_arg_func)(5)  # → 10
    """

    def uncurried(args_or_single: Tuple[Any, ...] | Any) -> T:
        if isinstance(args_or_single, (tuple, list)):
            return func(*args_or_single)
        else:
            # 对于非元组参数，尝试直接调用
            # 如果函数需要多个参数，会抛出 TypeError
            return func(args_or_single)

    return uncurried


def branch(spec: list | Callable[..., Any]) -> Callable[..., Any]:
    """从嵌套列表规范构建计算图。

    branch 提供了一种简洁的 DSL 来描述计算图，支持线性管道和复杂的分支合并。

    执行规则:
    1. 单个函数: 直接应用
    
    2. 纯函数列表 [f1, f2, ..., fn]（无嵌套列表）:
       - 作为线性管道处理：f_n(...f2(f1(x)))
       - 完全等同于 pipe(f1, f2, ..., fn)(x)
       - 例: [input, int, _+1, print](x) → print(_+1(int(input(x))))

    3. 包含嵌套列表的列表（分支合并）[branch1, [f1, f2], merge_func]:
       - branch1: 独立分支（应用于输入）
       - [f1, f2]: 嵌套列表作为 fork 分支（并行处理）
       - merge_func: 合并函数（参数来自前面的分支）
       - fork 产生的元组自动展开为 merge_func 的多个参数

    示例 1（简单管道，等价于 pipe）:
        branch([input, int, _+1, print])(99)
        # 向用户输入，转为整数，加1，打印结果

    示例 2（管道 + 分支合并）:
        # 原始代码: c(b1(a(x)), b2(b21(a(x)), b22(a(x))))
        branch([a, [b1, [b21, b22], b2], c])(x)
        
        执行流程：
          a(x) → y
          b1(y) → branch_result
          [b21, b22](y) → (b21(y), b22(y))  [产生元组]
          b2(*tuple_result) → merged         [uncurry展开]
          c(branch_result, merged) → final

    示例 3（简单的并行处理，不需要 branch）:
        # 直接使用 fork 函数更清晰
        fork(f1, f2)(x)  # → (f1(x), f2(x))
    """

    def process_item(spec_item: list | Callable[..., Any], value: Any, is_top_level: bool = True) -> Any:
        """递归处理规范项（函数或列表）。
        
        Args:
            is_top_level: 是否是顶层列表。
              - True: 纯函数列表 → 管道模式
              - False: 纯函数列表 → fork 模式（并行分发）
        """
        if callable(spec_item):
            return spec_item(value)

        elif isinstance(spec_item, list):
            if not spec_item:
                return value

            # 检查是否有嵌套列表
            has_nested = any(isinstance(elem, list) for elem in spec_item)

            if not has_nested:
                # 纯函数列表
                if is_top_level:
                    # 顶层 => 线性管道处理
                    # [f1, f2, f3](x) → f3(f2(f1(x)))
                    current = value
                    for elem in spec_item:
                        current = process_item(elem, current, is_top_level=False)
                    return current
                else:
                    # 嵌套位置 => fork 处理（并行分发）
                    # [f1, f2](x) → (f1(x), f2(x))
                    return tuple(process_item(elem, value, is_top_level=False) for elem in spec_item)

            else:
                # 包含嵌套列表 => merge 模式
                # 最后一个元素是 merge 函数
                merge_func = spec_item[-1]
                branches = spec_item[:-1]

                # 处理每个分支
                non_list_results = []
                fork_result = None

                for branch in branches:
                    if isinstance(branch, list):
                        # 嵌套列表分支（fork 处理）
                        fork_result = process_item(branch, value, is_top_level=False)
                    else:
                        # 函数分支
                        non_list_results.append(process_item(branch, value, is_top_level=False))

                # 构造 merge 函数的输入
                if fork_result is not None:
                    # 优先使用 fork 结果作为 merge 的输入
                    merged = uncurry(merge_func)(fork_result)
                elif non_list_results:
                    # 只有非列表分支
                    if len(non_list_results) == 1:
                        merged = merge_func(non_list_results[0])
                    else:
                        merged = uncurry(merge_func)(tuple(non_list_results))
                else:
                    # 没有分支，直接调用
                    merged = merge_func()

                # 返回格式：(所有非fork分支..., merge_result)
                if non_list_results:
                    return tuple(non_list_results) + (merged,)
                else:
                    return merged

        else:
            raise ValueError(f"Invalid spec item: {spec_item}")

    def process_pipeline(spec: list | Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """处理规范（可以是函数或列表）。
        
        如果没有参数，第一个函数自己处理（如 input()）。
        如果有参数，按正常流程处理。
        """
        if callable(spec):
            if args or kwargs:
                return spec(*args, **kwargs)
            else:
                return spec()

        if not isinstance(spec, list):
            raise ValueError(f"Invalid spec: {spec}")

        if not spec:
            return args[0] if args else None

        # 处理列表
        if not args and not kwargs:
            # 无参数：第一个函数自己处理
            first_stage = spec[0]
            if callable(first_stage):
                current = first_stage()  # 无参调用
            else:
                raise ValueError(f"Cannot call non-callable stage without input: {first_stage}")
            
            # 如果只有一个阶段，直接返回
            if len(spec) == 1:
                return current
            
            # 剩余阶段
            remaining_stages = spec[1:]
        else:
            # 有参数：第一个参数传给第一个阶段
            current = args[0] if args else None
            remaining_stages = spec

        # 处理剩余阶段（除了最后一个）
        for stage in remaining_stages[:-1]:
            current = process_item(stage, current, is_top_level=False)

        # 处理最后一个阶段
        last_stage = remaining_stages[-1]
        if callable(last_stage):
            # 如果前一个阶段产生了元组，自动 uncurry
            if isinstance(current, tuple):
                return uncurry(last_stage)(current)
            else:
                return last_stage(current)
        else:
            return process_item(last_stage, current, is_top_level=False)

    return lambda *args: process_pipeline(spec, *args)
