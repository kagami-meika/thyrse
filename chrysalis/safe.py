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

"""简单的安全容器（Safe / Result Monad），用于避免运行时异常中断链式表达式。

示例:
    result = safe(lambda: 1 / 0).fmap(lambda x: x + 1).unwrap_or(0)
    assert result == 0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Optional, TypeVar, Union

T = TypeVar("T")
U = TypeVar("U")


@dataclass(frozen=True)
class Safe(Generic[T]):
    """安全容器，封装可能会抛异常的计算结果。"""

    _value: Optional[T] = None
    _error: Optional[Exception] = None

    @property
    def ok(self) -> bool:
        return self._error is None

    @property
    def err(self) -> bool:
        return self._error is not None

    def fmap(self, fn: Callable[[T], U]) -> "Safe[U]":
        """对内部值进行映射，如果出错保持 error。"""

        if self.err:
            return Safe(_error=self._error)
        try:
            return Safe(_value=fn(self._value))  # type: ignore[arg-type]
        except Exception as e:
            return Safe(_error=e)

    def bind(self, fn: Callable[[T], "Safe[U]"]) -> "Safe[U]":
        """链式调用，函数必须返回 Safe。"""

        if self.err:
            return Safe(_error=self._error)
        try:
            return fn(self._value)  # type: ignore[arg-type]
        except Exception as e:
            return Safe(_error=e)

    def unwrap_or(self, default: U) -> Union[T, U]:
        """取出值或默认值。"""

        return self._value if self.ok else default

    def unwrap(self) -> T:
        """取出值，若有异常则重新抛出。"""

        if self.err:
            raise self._error  # type: ignore[union-attr]
        return self._value  # type: ignore[return-value]


def safe(fn: Callable[[], T]) -> Safe[T]:
    """将一个可能抛异常的计算包装为 Safe。"""

    try:
        return Safe(_value=fn())
    except Exception as e:
        return Safe(_error=e)
