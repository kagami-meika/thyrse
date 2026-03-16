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

"""代数数据类型与单子 (ADTs & Monads)。

提供 Maybe/Optional、Either/Result 等容器，用于优雅处理 None 和错误。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar, Union
import asyncio

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True)
class Optional(Generic[T]):
    """Maybe/Optional 单子：处理可能为 None 的值。

    该类型同时也用于支持 Python 结构化模式匹配（`match ... case Optional(value):`）。
    """

    _value: Optional[T]

    @classmethod
    def of(cls, value: T) -> "Optional[T]":
        return cls(_value=value)

    @classmethod
    def empty(cls) -> "Optional[T]":
        return Nothing()

    def fmap(self, fn: Callable[[T], U]) -> "Optional[U]":
        if self._value is None:
            return Optional.empty()
        return Optional.of(fn(self._value))

    def bind(self, fn: Callable[[T], "Optional[U]"]) -> "Optional[U]":
        if self._value is None:
            return Optional.empty()
        return fn(self._value)

    def get_or_else(self, default: U) -> Union[T, U]:
        return self._value if self._value is not None else default

    def is_present(self) -> bool:
        return self._value is not None


class Nothing:
    """Empty / None 变体 (用于模式匹配)。"""

    __match_args__: tuple = ()

    _instance: "Nothing" | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def fmap(self, fn: Callable[[Any], Any]) -> "Nothing":
        return self

    def bind(self, fn: Callable[[Any], "Nothing"]) -> "Nothing":
        return self

    def get_or_else(self, default: Any) -> Any:
        return default

    def is_present(self) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "Nothing"


# 提供更符合模式匹配命名的别名
Some = Optional


class Result(Generic[T]):
    """Either/Result 单子：处理成功或失败的值。

    该类型伴随 `Ok` / `Err` 两个变体，可直接用于结构化模式匹配。
    """

    @classmethod
    def ok(cls, value: T) -> "Ok[T]":
        return Ok(value)

    @classmethod
    def err(cls, error: Exception) -> "Err[T]":
        return Err(error)


@dataclass(frozen=True)
class Ok(Result[T]):
    value: T

    def fmap(self, fn: Callable[[T], U]) -> "Ok[U]":
        return Ok(fn(self.value))

    def bind(self, fn: Callable[[T], "Result[U]"]) -> "Result[U]":
        return fn(self.value)

    def unwrap_or(self, default: U) -> Union[T, U]:
        return self.value

    def unwrap(self) -> T:
        return self.value


@dataclass(frozen=True)
class Err(Result[T]):
    error: Exception

    def fmap(self, fn: Callable[[T], U]) -> "Err[U]":
        return self  # type: ignore[return-value]

    def bind(self, fn: Callable[[T], "Result[U]"]) -> "Err[U]":
        return self  # type: ignore[return-value]

    def unwrap_or(self, default: U) -> Union[T, U]:
        return default

    def unwrap(self) -> T:
        raise self.error


class AsyncResult(Generic[T]):
    """异步 Either/Result 单子：处理异步成功或失败的值。

    伴随 `AsyncOk` / `AsyncErr` 两个变体。
    """

    @classmethod
    def ok(cls, value: T) -> "AsyncOk[T]":
        return AsyncOk(value)

    @classmethod
    def err(cls, error: Exception) -> "AsyncErr[T]":
        return AsyncErr(error)


@dataclass(frozen=True)
class AsyncOk(AsyncResult[T]):
    value: T

    async def fmap(self, fn: Callable[[T], U]) -> "AsyncOk[U]":
        result = fn(self.value)
        if asyncio.iscoroutine(result):
            return AsyncOk(await result)
        return AsyncOk(result)

    async def bind(self, fn: Callable[[T], Awaitable["AsyncResult[U]"]]) -> "AsyncResult[U]":
        return await fn(self.value)

    async def unwrap_or(self, default: U) -> Union[T, U]:
        return self.value

    async def unwrap(self) -> T:
        return self.value


@dataclass(frozen=True)
class AsyncErr(AsyncResult[T]):
    error: Exception

    async def fmap(self, fn: Callable[[T], U]) -> "AsyncErr[U]":
        return self  # type: ignore[return-value]

    async def bind(self, fn: Callable[[T], Awaitable["AsyncResult[U]"]]) -> "AsyncErr[U]":
        return self  # type: ignore[return-value]

    async def unwrap_or(self, default: U) -> Union[T, U]:
        return default

    async def unwrap(self) -> T:
        raise self.error


# 透镜相关工具移至 fpll.lens 模块，保留此处以维持向后兼容。
from .lens import path, over  # noqa: F401
