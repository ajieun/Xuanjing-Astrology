"""紫微斗数排盘：直接复用 mingli-master 的确定性计算管线。"""
import datetime
import os
import tempfile

from .resources import load_vendor_module, vendor_mingli

_SCRIPTS_DIR = vendor_mingli("scripts")
_CACHE = {}

HOUR_NAMES = {
    0: "早子时 (23:00-00:00)", 1: "丑时 (01:00-03:00)", 2: "寅时 (03:00-05:00)",
    3: "卯时 (05:00-07:00)", 4: "辰时 (07:00-09:00)", 5: "巳时 (09:11)",
    6: "午时 (11:00-13:00)", 7: "未时 (13:00-15:00)", 8: "申时 (15:00-17:00)",
    9: "酉时 (17:00-19:00)", 10: "戌时 (19:00-21:00)", 11: "亥时 (21:00-23:00)",
    12: "晚子时 (23:00-00:00)",
}

BRANCH_GRID = [
    ("巳", 0, 0), ("午", 0, 1), ("未", 0, 2), ("申", 0, 3),
    ("辰", 1, 0), ("酉", 1, 3),
    ("卯", 2, 0), ("戌", 2, 3),
    ("寅", 3, 0), ("丑", 3, 1), ("子", 3, 2), ("亥", 3, 3),
]


def _module(name):
    if name not in _CACHE:
        _CACHE[name] = load_vendor_module(_SCRIPTS_DIR, name)
    return _CACHE[name]


def build_chart(date_str, hour_index, gender, is_lunar=False, is_leap=False, target_year=None):
    """返回完整的排盘 dict（含格局判定与流年压力审计）。"""
    calculator = _module("calculate_chart")
    year = target_year or datetime.date.today().year
    chart = calculator.build_chart(date_str, int(hour_index), gender, is_lunar, is_leap)
    return calculator.enrich_chart(chart, int(year))


def empty_reading():
    return {"cards": [], "hand_reading": {"items": []}, "calibration_questions": []}


def calibration_pool(limit=8):
    try:
        calibration = _module("calibration")
        questions = list(getattr(calibration, "CALIBRATION_QUESTIONS", []))
    except Exception:  # noqa: BLE001 - 题库缺失不应阻塞排盘
        return []
    picked = [q for q in questions if q.get("priority") == "high"]
    picked += [q for q in questions if q.get("priority") != "high"]
    return picked[:limit]


def render_html(chart_data, reading_data):
    """调用 mingli-master 的模板引擎生成可视化命盘 HTML，返回文件路径。"""
    generator = _module("generate_html")
    template = vendor_mingli("templates", "chart_template.html")
    html = generator.generate_html(chart_data, reading_data, template)

    name = "命盘"
    if chart_data.get("solar_date"):
        name = f"命盘-{chart_data['solar_date']}"
    path = os.path.join(tempfile.gettempdir(), f"mingpan-{os.getpid()}-{abs(hash(name)) % 100000}.html")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(html)
    return path


def soul_palace(chart_data):
    return next((p for p in chart_data["palaces"] if "命宫" in p.get("tags", [])), None)


def palace_by_branch(chart_data):
    return {p["earthly_branch"]: p for p in chart_data["palaces"]}
