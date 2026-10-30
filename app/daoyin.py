"""道家术数：四柱八字、三元九运、建除十二神、二十八宿择日参考。"""
from lunar_python import Solar

TIANGAN = "甲乙丙丁戊己庚辛壬癸"
DIZHI = "子丑寅卯辰巳午未申酉戌亥"

WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
    "寅": "木", "卯": "木", "巳": "火", "午": "火", "申": "金",
    "酉": "金", "亥": "水", "子": "水", "辰": "土", "戌": "土",
    "丑": "土", "未": "土",
}

SHISHEN = {
    "木木": "比肩", "木火": "食神", "木土": "偏财", "木金": "七杀", "木水": "偏印",
    "火木": "正印", "火火": "比肩", "火土": "伤官", "火金": "正财", "火水": "七杀",
    "土木": "正官", "土火": "正印", "土土": "比肩", "土金": "伤官", "土水": "正财",
    "金木": "正财", "金火": "正官", "金土": "偏印", "金金": "比肩", "金水": "食神",
    "水木": "伤官", "水火": "偏财", "水土": "正官", "水金": "偏印", "水水": "比肩",
}

# 三元九运：1864 年起上元一运，每运 20 年
YUN_TABLE = [
    ("一运", "一白贪狼", "坎", "水"),
    ("二运", "二黑巨门", "坤", "土"),
    ("三运", "三碧禄存", "震", "木"),
    ("四运", "四绿文曲", "巽", "木"),
    ("五运", "五黄廉贞", "中", "土"),
    ("六运", "六白武曲", "乾", "金"),
    ("七运", "七赤破军", "兑", "金"),
    ("八运", "八白左辅", "艮", "土"),
    ("九运", "九紫右弼", "离", "火"),
]

JIANCHU = ["建", "除", "满", "平", "定", "执", "破", "危", "成", "收", "开", "闭"]

JIANCHU_NOTE = {
    "建": "宜开局、立新；忌大动干戈。",
    "除": "宜扫尘、除旧、疗疾。",
    "满": "宜收成、纳财；忌冒进。",
    "平": "宜修造、调和、立约。",
    "定": "宜定盟、安床、守成。",
    "执": "宜执事、捕捉；忌搬迁。",
    "破": "宜破旧、拆解；忌开张嫁娶。",
    "危": "宜静守、祭祀；忌冒险。",
    "成": "宜成事、嫁娶、开业。",
    "收": "宜收纳、进仓、讨账。",
    "开": "宜开市、开工、出行。",
    "闭": "宜闭门、收敛、筑堤。",
}

# 二十八宿（角亢氐房心尾箕 / 斗牛女虚危室壁 / 奎娄胃昴毕觜参 / 井鬼柳星张翼轸）
MANSIONS = [
    ("角", "木", "蛟"), ("亢", "金", "龙"), ("氐", "土", "貉"), ("房", "日", "兔"),
    ("心", "月", "狐"), ("尾", "火", "虎"), ("箕", "水", "豹"),
    ("斗", "木", "獬"), ("牛", "金", "牛"), ("女", "土", "蝠"), ("虚", "日", "鼠"),
    ("危", "月", "燕"), ("室", "火", "猪"), ("壁", "水", "貐"),
    ("奎", "木", "狼"), ("娄", "金", "狗"), ("胃", "土", "雉"), ("昴", "日", "鸡"),
    ("毕", "月", "乌"), ("觜", "火", "猴"), ("参", "水", "猿"),
    ("井", "木", "犴"), ("鬼", "金", "羊"), ("柳", "土", "獐"), ("星", "日", "马"),
    ("张", "月", "鹿"), ("翼", "火", "蛇"), ("轸", "水", "蚓"),
]


def shishen(day_master, other):
    return SHISHEN.get(WUXING.get(day_master, "") + WUXING.get(other, ""), "—")


def fortune_period(year):
    """三元九运：返回 (运名, 星名, 卦, 五行)。"""
    index = (int(year) - 1864) // 20 % 9
    return YUN_TABLE[index]


def jianchu(month_branch, day_branch):
    """建除十二神：月建起建，顺行至日支。"""
    if month_branch not in DIZHI or day_branch not in DIZHI:
        return "", ""
    offset = (DIZHI.index(day_branch) - DIZHI.index(month_branch)) % 12
    name = JIANCHU[offset]
    return name, JIANCHU_NOTE.get(name, "")


def mansion(day_branch):
    """二十八宿参考：以日支所在宿位顺排，作为择日的粗略参考。"""
    if day_branch not in DIZHI:
        return "", "", ""
    index = DIZHI.index(day_branch) % 7
    name, element, animal = MANSIONS[index]
    return name, element, animal


def count_wuxing(pillars):
    counter = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for pillar in pillars:
        for char in pillar:
            element = WUXING.get(char)
            if element:
                counter[element] += 1
    return counter


def compute_bazi(year, month, day, hour, minute=0, gender="男"):
    """计算四柱八字与道家择日参考项。"""
    solar = Solar.fromYmdHms(int(year), int(month), int(day), int(hour), int(minute), 0)
    lunar = solar.getLunar()
    eight = lunar.getEightChar()

    pillars = [
        ("年柱", eight.getYear(), eight.getYearShiShenGan(), eight.getYearWuXing(), eight.getYearNaYin(), eight.getYearXunKong()),
        ("月柱", eight.getMonth(), eight.getMonthShiShenGan(), eight.getMonthWuXing(), eight.getMonthNaYin(), eight.getMonthXunKong()),
        ("日柱", eight.getDay(), eight.getDayShiShenGan(), eight.getDayWuXing(), eight.getDayNaYin(), eight.getDayXunKong()),
        ("时柱", eight.getTime(), eight.getTimeShiShenGan(), eight.getTimeWuXing(), eight.getTimeNaYin(), eight.getTimeXunKong()),
    ]

    day_master = eight.getDayGan()
    counter = count_wuxing([p[1] for p in pillars])
    month_branch = eight.getMonthZhi()
    day_branch = eight.getDayZhi()

    try:
        yun = eight.getYun(1 if gender == "男" else 0)
        qiyun = f"{yun.getStartYear()}年{yun.getStartMonth()}月{yun.getStartDay()}日起运"
    except Exception:  # noqa: BLE001 - 起运信息缺失不影响主结果
        qiyun = "起运信息不可用"

    jc_name, jc_note = jianchu(month_branch, day_branch)
    mansion_name, mansion_element, mansion_animal = mansion(day_branch)
    period, star, trigram, period_element = fortune_period(year)

    return {
        "solar": f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
        "lunar": f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}",
        "ganzhi": f"{lunar.getYearInGanZhiExact()}年 {lunar.getMonthInGanZhiExact()}月 {lunar.getDayInGanZhiExact()}日 {lunar.getTimeInGanZhi()}时",
        "jieqi": lunar.getPrevJieQi().getName() if lunar.getPrevJieQi() else "",
        "day_master": day_master,
        "day_master_element": WUXING.get(day_master, "—"),
        "pillars": pillars,
        "wuxing": counter,
        "qiyun": qiyun,
        "fortune_period": {
            "period": period,
            "star": star,
            "trigram": trigram,
            "element": period_element,
            "year": year,
        },
        "jianchu": {"name": jc_name, "note": jc_note, "month_branch": month_branch},
        "mansion": {"name": mansion_name, "element": mansion_element, "animal": mansion_animal},
        "hide_gan": {
            "年": eight.getYearHideGan(),
            "月": eight.getMonthHideGan(),
            "日": eight.getDayHideGan(),
            "时": eight.getTimeHideGan(),
        },
    }
