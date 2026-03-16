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
