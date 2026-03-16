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

"""透镜（Lens）工具：支持安全、不可变地深层更新对象结构。

本模块提供了一套 Lens API，可在不修改原始数据的情况下读取/写入深层嵌套结构
（支持 dict、list/tuple、dataclass、普通对象）。

示例用法：
    from fpll.lens import lens_path, view, set_, over

    data = {"user": {"profile": {"email": "a@b.com"}}}
    email_lens = lens_path("user.profile.email")
    assert view(email_lens, data) == "a@b.com"
    updated = set_(email_lens, "x@y.com", data)
    assert data["user"]["profile"]["email"] == "a@b.com"
    assert updated["user"]["profile"]["email"] == "x@y.com"
"""

from __future__ import annotations

import copy
import dataclasses
from dataclasses import is_dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence, TypeVar, Union

T = TypeVar("T")
U = TypeVar("U")

__all__ = [
    "Lens",
    "lens",
    "lens_path",
    "path",
    "lens_key",
    "lens_index",
    "lens_attr",
    "view",
    "set_",
    "over",
]


class Lens:
    """表示可组合的取值/设值对（透镜）。"""

    __slots__ = ("get", "set")

    def __init__(self, get: Callable[[Any], Any], set: Callable[[Any, Any], Any]) -> None:
        self.get = get
        self.set = set

    def over(self, fn: Callable[[Any], Any], obj: Any) -> Any:
        """对透镜聚焦的值应用函数，并返回更新后的新结构。"""

        return set_(self, fn(self.get(obj)), obj)


def lens(get: Callable[[Any], Any], set: Callable[[Any, Any], Any]) -> Lens:
    """从 getter 和 setter 创建一个透镜。"""

    return Lens(get, set)


def view(ln: Lens, obj: Any) -> Any:
    """从对象中读取透镜聚焦的值（只读）。"""

    return ln.get(obj)


def set_(ln: Lens, value: Any, obj: Any) -> Any:
    """在不修改原对象的前提下，返回设置了新值的对象副本。"""

    return ln.set(value, obj)


def over(ln: Lens, fn: Callable[[Any], Any], obj: Any) -> Any:
    """对聚焦的值应用 fn，并返回更新后的新结构（不可变操作）。"""

    return ln.set(fn(ln.get(obj)), obj)


def _normalize_path(path: Union[str, Iterable[Union[str, int]]]) -> list[Union[str, int]]:
    """把点号路径或可迭代路径标准化为 key 列表。

    支持字符串形式如 "a.b.0.c"（数字自动转换为 int）。
    """

    if isinstance(path, str):
        # 支持 "a.b.0.c" 形式，允许额外空格
        parts = [p for p in path.strip().split(".") if p != ""]
        normalized: list[Union[str, int]] = []
        for p in parts:
            if p.isdigit():
                normalized.append(int(p))
            else:
                normalized.append(p)
        return normalized

    return list(path)


def _assoc_in(obj: Any, keys: list[Union[str, int]], value: Any) -> Any:
    """不可变的深层更新辅助函数（类似 Clojure 的 assoc-in）。"""

    if not keys:
        return value

    key, *rest = keys

    # dict / Mapping 类型
    if isinstance(obj, Mapping):
        new_obj = dict(obj)
        new_obj[key] = _assoc_in(obj.get(key), rest, value)
        return new_obj

    # 序列类型（list/tuple）
    if isinstance(obj, (list, tuple)) and isinstance(key, int):
        if 0 <= key < len(obj):
            new_seq = list(obj)
            new_seq[key] = _assoc_in(obj[key], rest, value)
            return tuple(new_seq) if isinstance(obj, tuple) else new_seq
        # 索引越界视为安全操作：返回原始对象
        return obj

    # dataclass 实例
    if is_dataclass(obj):
        try:
            fields = {f.name: getattr(obj, f.name) for f in dataclasses.fields(obj)}
            if rest:
                current = getattr(obj, key, None)
                fields[key] = _assoc_in(current, rest, value)
            else:
                fields[key] = value
            return dataclasses.replace(obj, **fields)
        except Exception:
            return obj

    # 通用对象：尝试浅拷贝并设置属性
    if obj is None:
        # 如果路径中间出现 None，则回退到构建 dict 嵌套链
        if rest:
            return {key: _assoc_in(None, rest, value)}
        return {key: value}

    try:
        new_obj = copy.copy(obj)
        if rest:
            current = getattr(obj, key, None)
            setattr(new_obj, key, _assoc_in(current, rest, value))
        else:
            setattr(new_obj, key, value)
        return new_obj
    except Exception:
        return obj


def lens_key(key: Any) -> Lens:
    """聚焦于 dict 的某个 key。"""

    return lens(lambda obj: obj.get(key) if isinstance(obj, Mapping) else None, lambda v, obj: _assoc_in(obj, [key], v))


def lens_index(idx: int) -> Lens:
    """聚焦于 list/tuple 的某个索引。"""

    def _get(obj: Any) -> Any:
        try:
            return obj[idx]
        except Exception:
            return None

    def _set(v: Any, obj: Any) -> Any:
        return _assoc_in(obj, [idx], v)

    return lens(_get, _set)


def lens_attr(name: str) -> Lens:
    """聚焦于对象的某个属性。"""

    def _get(obj: Any) -> Any:
        return getattr(obj, name, None)

    def _set(v: Any, obj: Any) -> Any:
        return _assoc_in(obj, [name], v)

    return lens(_get, _set)


def lens_path(path: Union[str, Iterable[Union[str, int]]]) -> Lens:
    """根据 dot-path（如 "a.b.0.c"）或 key 列表创建透镜。"""

    keys = _normalize_path(path)

    def _get(obj: Any) -> Any:
        current = obj
        for key in keys:
            if current is None:
                return None
            try:
                if isinstance(current, Mapping):
                    current = current.get(key)
                elif isinstance(current, (list, tuple)) and isinstance(key, int):
                    current = current[key] if 0 <= key < len(current) else None
                else:
                    current = getattr(current, key, None)
            except Exception:
                return None
        return current

    def _set(v: Any, obj: Any) -> Any:
        return _assoc_in(obj, keys, v)

    return lens(_get, _set)


# 兼容旧 API
path = lens_path
