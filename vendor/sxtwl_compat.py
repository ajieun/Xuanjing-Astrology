"""《sxtwl》兼容适配层。

`ichingshifa` 依赖带原生扩展的 `sxtwl` 做公历转农历与干支换算，
Windows 上往往没有可用的编译环境或预编译轮。本模块用纯 Python 的
`lunar_python` 实现 `ichingshifa` 实际调用到的那部分接口，
让周易筮法可以随 exe 一起分发，而不要求用户安装编译工具链。

只实现被调用到的成员：
    fromSolar(year, month, day)
        -> getLunarYear() / getLunarMonth() / getLunarDay()
        -> getYearGZ() / getMonthGZ() / getDayGZ() / getHourGZ(hour)
"""
import itertools
import sys
import types

from lunar_python import Solar

TIANGAN = "甲乙丙丁戊己庚辛壬癸"
DIZHI = "子丑寅卯辰巳午未申酉戌亥"

# 五鼠遁：日干起子时
FIVE_RATS = {
    "甲": "甲子", "己": "甲子",
    "乙": "丙子", "庚": "丙子",
    "丙": "戊子", "辛": "戊子",
    "丁": "庚子", "壬": "庚子",
    "戊": "壬子", "癸": "壬子",
}


class _GanZhi:
    """模拟 sxtwl 的干支对象：只提供天干/地支索引。"""

    __slots__ = ("tg", "dz", "ganzhi")

    def __init__(self, ganzhi):
        self.ganzhi = ganzhi
        self.tg = TIANGAN.index(ganzhi[0])
        self.dz = DIZHI.index(ganzhi[1])

    def __repr__(self):
        return self.ganzhi


class _Day:
    """模拟 sxtwl 的日对象。"""

    __slots__ = ("lunar", "year_gz", "month_gz", "day_gz")

    def __init__(self, year, month, day):
        self.lunar = Solar.fromYmd(year, month, day).getLunar()
        self.year_gz = self.lunar.getYearInGanZhiExact()
        self.month_gz = self.lunar.getMonthInGanZhiExact()
        self.day_gz = self.lunar.getDayInGanZhiExact()

    def getLunarYear(self):
        return self.lunar.getYear()

    def getLunarMonth(self):
        return abs(self.lunar.getMonth())

    def getLunarDay(self):
        return self.lunar.getDay()

    def getYearGZ(self):
        return _GanZhi(self.year_gz)

    def getMonthGZ(self):
        return _GanZhi(self.month_gz)

    def getDayGZ(self):
        return _GanZhi(self.day_gz)

    def getHourGZ(self, hour):
        start = FIVE_RATS[self.day_gz[0]]
        offset = (int(hour) // 2) % 12
        stem = TIANGAN[(TIANGAN.index(start[0]) + offset) % 10]
        branch = DIZHI[(DIZHI.index(start[1]) + offset) % 12]
        return _GanZhi(stem + branch)


def fromSolar(year, month, day):
    return _Day(year, month, day)


def install():
    """把本模块注册成 `sxtwl`。若本机已有真正的 sxtwl 则原样保留。"""
    try:
        import sxtwl  # noqa: F401
        return False
    except Exception:
        pass

    shim = sys.modules.get("sxtwl")
    if shim is not None and getattr(shim, "__mingpan_shim__", False):
        return True

    module = types.ModuleType("sxtwl")
    module.__mingpan_shim__ = True
    module.fromSolar = fromSolar
    module.GanZhi = _GanZhi
    module.Day = _Day
    module.TIANGAN = TIANGAN
    module.DIZHI = DIZHI
    sys.modules["sxtwl"] = module
    return True


assert itertools  # 保持导入稳定，便于静态检查
