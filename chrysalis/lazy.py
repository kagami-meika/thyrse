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

"""惰性求值（thunks）与延迟计算的小工具。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import wraps
from threading import Lock
from typing import Any, Awaitable, Callable, Generic, TypeVar

T = TypeVar("T")

__all__ = ["thunk", "force", "Lazy", "AsyncLazy"]


def thunk(fn: Callable[[], T]) -> Callable[[], T]:
    """把函数封装成惰性求值的 thunk。"""

    @wraps(fn)
    def _inner() -> T:
        return fn()

    return _inner


def force(t: Callable[[], T]) -> T:
    """强制求值一个 thunk。"""

    return t()


@dataclass
class Lazy(Generic[T]):
    """惰性求值包装器。

    使用示例:
        x = Lazy(lambda: expensive())
        y = x.value  # 仅在这里求值一次
    """

    _fn: Callable[[], T]
    _cached: Any = None
    _evaluated: bool = False
    _lock: Lock = None  # type: ignore[assignment]

    def __post_init__(self):
        if self._lock is None:
            self._lock = Lock()

    @property
    def value(self) -> T:
        with self._lock:
            if not self._evaluated:
                self._cached = self._fn()
                self._evaluated = True
        return self._cached

    def map(self, fn: Callable[[T], Any]) -> "Lazy":
        return Lazy(lambda: fn(self.value))


@dataclass
class AsyncLazy(Generic[T]):
    """异步惰性求值包装器（线程安全）。

    使用示例:
        x = AsyncLazy(lambda: await expensive_async())
        y = await x.value  # 仅在这里异步求值一次
    """

    _fn: Callable[[], Awaitable[T]]
    _cached: Any = None
    _evaluated: bool = False
    _lock: asyncio.Lock = None  # type: ignore[assignment]

    def __post_init__(self):
        if self._lock is None:
            self._lock = asyncio.Lock()

    @property
    async def value(self) -> T:
        async with self._lock:
            if not self._evaluated:
                self._cached = await self._fn()
                self._evaluated = True
        return self._cached

    def map(self, fn: Callable[[T], Awaitable[Any]]) -> "AsyncLazy":
        async def _mapped():
            return await fn(await self.value)
        return AsyncLazy(_mapped)
