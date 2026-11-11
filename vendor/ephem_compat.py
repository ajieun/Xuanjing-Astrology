"""《ephem.Date》最小兼容层。

`ichingshifa` 依赖 PyEphem 的 Date 类，用于：
1. 解析 "YYYY/MM/DD HH:MM:SS" 格式字符串
2. 提供 .tuple() 方法返回 (y, m, d, h, m, s)
3. 支持 round(Date(...)) 取整儒略日

用纯 Python 实现，无需 C 编译。
"""
import re
from datetime import datetime


def Date(value=None, precision=None):
    """模拟 ephem.Date 的最小接口。"""
    if value is None:
        # Date() -> 当前时刻
        dt = datetime.now()
    elif isinstance(value, str):
        # Date("YYYY/MM/DD HH:MM:SS")
        value = value.strip()
        # 支持 "2024/01/15 23:00:00.00" 格式
        match = re.match(
            r"(\d{4})/(\d{1,2})/(\d{1,2})(?:\s+(\d{1,2}):(\d{1,2}):(\d{1,2})(?:\.\d+)?)?",
            value,
        )
        if not match:
            raise ValueError(f"Cannot parse date string: {value!r}")
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4) or 0)
        minute = int(match.group(5) or 0)
        second = int(match.group(6) or 0)
        dt = datetime(year, month, day, hour, minute, second)
    elif isinstance(value, datetime):
        dt = value
    else:
        raise TypeError(f"Unsupported Date value: {type(value)}")

    return _DateWrapper(dt)


class _DateWrapper:
    """包装 datetime，提供 ephem.Date 接口。"""

    def __init__(self, dt: datetime):
        self._dt = dt

    def tuple(self):
        """返回 (year, month, day, hour, minute, second) 元组。"""
        return (
            self._dt.year,
            self._dt.month,
            self._dt.day,
            self._dt.hour,
            self._dt.minute,
            float(self._dt.second),
        )

    def __round__(self, ndigits=None):
        """round(Date(...)) 取整到天。"""
        from lunar_python import Solar

        s = Solar.fromYmdHms(
            self._dt.year, self._dt.month, self._dt.day,
            self._dt.hour, self._dt.minute, self._dt.second,
        )
        jd = s.getJulianDay()
        jd = round(jd)

        # 从整数儒略日创建新 Date
        return _DateWrapper(self._dt.__class__(
            self._dt.year, self._dt.month, self._dt.day
        ))

    def __repr__(self):
        return f"Date({self._dt.isoformat()!r})"
