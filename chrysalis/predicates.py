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

"""谓词逻辑与属性化的工具函数。"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping, TypeVar

T = TypeVar("T")

__all__ = [
    "prop",
    "get",
    "has",
    "is_type",
    "and_",
    "or_",
    "not_",
    "truthy",
    "falsy",
]


def prop(name: str, default: Any = None) -> Callable[[Any], Any]:
    """返回从对象/字典取属性/键的函数。"""

    def _getter(obj: Any) -> Any:
        if obj is None:
            return default
        if isinstance(obj, Mapping):
            return obj.get(name, default)
        return getattr(obj, name, default)

    return _getter


def get(index: int, default: Any = None) -> Callable[[Iterable[Any]], Any]:
    """从可迭代对象取 index 项。"""

    def _getter(it: Iterable[Any]) -> Any:
        try:
            return list(it)[index]
        except Exception:
            return default

    return _getter


def has(name: str) -> Callable[[Any], bool]:
    """检查对象是否含有某个属性/键。"""

    def _checker(obj: Any) -> bool:
        if obj is None:
            return False
        if isinstance(obj, Mapping):
            return name in obj
        return hasattr(obj, name)

    return _checker


def get_in(obj: Any, path: str | Iterable[str], default: Any = None) -> Any:
    """从嵌套结构中取值，支持点号路径（"a.b.c"）。

    如果访问链中出现 None、KeyError/IndexError/AttributeError，则返回 default。
    """

    if isinstance(path, str):
        path = path.strip().split(".")

    current = obj
    for key in path:
        if current is None:
            return default
        try:
            if isinstance(current, Mapping):
                current = current[key]
            else:
                current = getattr(current, key)
        except Exception:
            return default
    return current


def is_type(t: type) -> Callable[[Any], bool]:
    """类型检查谓词。"""

    def _checker(obj: Any) -> bool:
        return isinstance(obj, t)

    return _checker


def and_(*preds: Callable[[T], bool]) -> Callable[[T], bool]:
    """逻辑与组合谓词。"""

    def _checker(x: T) -> bool:
        return all(p(x) for p in preds)

    return _checker


def or_(*preds: Callable[[T], bool]) -> Callable[[T], bool]:
    """逻辑或组合谓词。"""

    def _checker(x: T) -> bool:
        return any(p(x) for p in preds)

    return _checker


def not_(pred: Callable[[T], bool]) -> Callable[[T], bool]:
    """逻辑非谓词。"""

    def _checker(x: T) -> bool:
        return not pred(x)

    return _checker


def truthy(x: Any) -> bool:
    """真值判断谓词 (用于可组合逻辑)。"""

    return bool(x)


def falsy(x: Any) -> bool:
    """假值判断谓词 (用于可组合逻辑)。"""

    return not bool(x)
