"""周易筮法：大衍蓍草、铜钱与手动起卦。"""
import sys

from .resources import vendor

if vendor() not in sys.path:
    sys.path.insert(0, vendor())

from vendor.sxtwl_compat import install as _install_sxtwl  # noqa: E402

_install_sxtwl()

from ichingshifa import ichingshifa  # noqa: E402

_LINE_VALUE_NAME = {
    6: "老阴（动爻）",
    7: "少阳",
    8: "少阴",
    9: "老阳（动爻）",
}

# 爻符：由下而上
_LINE_GLYPH = {
    6: "▅▅　▅▅",
    7: "▅▅▅▅▅",
    8: "▅▅　▅▅",
    9: "▅▅▅▅▅",
}

_MONS_FULL = {"龍": "青龙", "雀": "朱雀", "陳": "勾陈", "蛇": "螣蛇", "虎": "白虎", "武": "玄武"}


def _engine():
    return ichingshifa.Iching()


def manual(lines):
    """手动起卦：lines 为 6 位字符串，由初爻到上爻，取值为 6/7/8/9。"""
    return _engine().mget_bookgua_details(lines)


def stalks():
    """大衍筮法随机起卦（模拟蓍草十八变）。"""
    return _engine().bookgua_details()


def coins():
    """铜钱起卦：三枚铜钱摇六次，等价于 6/7/8/9 的概率模型。"""
    import random

    values = []
    for _ in range(6):
        # 每枚铜钱：3 为字面（阴）、2 为背（阳），和为 6/7/8/9
        total = sum(random.choice((2, 3)) for _ in range(3))
        values.append(total)
    return manual("".join(str(v) for v in values))


def by_datetime(year, month, day, hour):
    """按指定年月日时起卦。"""
    return _engine().datetime_bookgua(int(year), int(month), int(day), int(hour))


def qigua_now():
    """按当前时刻起卦（含纳甲排盘）。"""
    return _engine().qigua_now()


def decode_gua(lines, rizhi):
    """手动排本卦纳甲。"""
    return _engine().decode_gua(lines, rizhi)


def normalize(raw):
    """把库的原始返回整理成界面友好的结构。"""
    if isinstance(raw, dict) and "大衍筮法" in raw:
        return _normalize_qigua(raw)
    return _normalize_lines(raw)


def _lines_from_raw(raw):
    if isinstance(raw, (list, tuple)) and raw:
        return str(raw[0])
    if isinstance(raw, dict):
        for key in ("卦爻", "lines", "大衍筮法"):
            value = raw.get(key)
            if isinstance(value, (list, tuple)) and value:
                return str(value[0])
            if isinstance(value, str):
                return value
    return ""


def _normalize_lines(raw):
    line_values = _lines_from_raw(raw)
    ben_gua = zhi_gua = ""
    texts = {}
    advice = []
    if isinstance(raw, (list, tuple)):
        if len(raw) > 1:
            ben_gua = raw[1]
        if len(raw) > 2:
            zhi_gua = raw[2]
        if len(raw) > 3 and isinstance(raw[3], dict):
            texts = raw[3]
        if len(raw) > 4 and raw[4]:
            advice = [str(item) for item in raw[4]]
    return {
        "lines": line_values,
        "ben_gua": ben_gua,
        "zhi_gua": zhi_gua,
        "texts": texts,
        "advice": advice,
        "najia": {},
        "date": "",
    }


def _normalize_qigua(raw):
    inner = raw.get("大衍筮法") or []
    base = _normalize_lines(inner)
    result = dict(base)
    result["date"] = raw.get("日期", "")
    najia = {}
    for key in ("本卦", "之卦"):
        block = raw.get(key) or {}
        if not block:
            continue
        najia[key] = {
            "name": block.get("卦", ""),
            "najia": block.get("納甲", []),
            "wuxing": block.get("五行", []),
            "liuqin": block.get("六親用神", []),
            "mons": [_MONS_FULL.get(m, m) for m in block.get("六獸", [])],
            "extra": {k: v for k, v in block.items()
                      if k not in ("卦", "納甲", "五行", "六親用神", "六獸")},
        }
    result["najia"] = najia
    result["ben_gua"] = najia.get("本卦", {}).get("name", result.get("ben_gua", ""))
    result["zhi_gua"] = najia.get("之卦", {}).get("name", result.get("zhi_gua", ""))
    return result


def line_detail(lines):
    """返回由下而上的爻列表，供界面绘制。"""
    detail = []
    for index, char in enumerate(str(lines)):
        try:
            value = int(char)
        except ValueError:
            continue
        detail.append({
            "index": index,
            "value": value,
            "name": _LINE_VALUE_NAME.get(value, str(value)),
            "glyph": _LINE_GLYPH.get(value, ""),
            "moving": value in (6, 9),
        })
    return detail


def texts_preview(texts):
    """把卦爻辞整理成可读文本。"""
    if not isinstance(texts, dict):
        return ""
    parts = []
    for key in sorted(texts, key=lambda k: (isinstance(k, str), k)):
        parts.append(f"{key}：{texts[key]}")
    return "\n".join(parts)
