"""塔罗牌：78 张完整牌组 + 经典牌阵（含凯尔特十字）。

牌义为韦特（Rider-Waite-Smith）体系通行的中文释义，
正逆位由本地随机洗牌决定；同一种子得到同一副牌，便于复现。
"""
import random

SUITS = [
    ("权杖", "Wands", "火", "♣"),
    ("圣杯", "Cups", "水", "♥"),
    ("宝剑", "Swords", "风", "♠"),
    ("星币", "Pentacles", "土", "♦"),
]

ROMAN = ["0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI"]

# 大阿卡纳：(序号, 中文名, 英文名, 关键词, 正位牌义, 逆位牌义, 星象/元素)
MAJOR_ARCANA = [
    (0, "愚人", "The Fool", "开始·冒险·天真", "新的循环正在打开，放下包袱去试一次，你比想象中自由。",
     "空有冲动而缺少落地计划，或在该承担时选择了逃避。", "风"),
    (1, "魔术师", "The Magician", "意志·显化·资源", "手上已有足够资源，缺的只是把它们串起来的那一下决心。",
     "话术多于行动，或被自己的聪明耽误了事。", "水星"),
    (2, "女祭司", "The High Priestess", "直觉·潜意识·守密", "答案在内不在外，先安静下来听直觉，有些事暂时不必说破。",
     "忽略内在声音，或被表象和流言牵着走。", "月亮"),
    (3, "皇后", "The Empress", "丰盛·滋养·创造", "是产出与收获的时期，把事养大，也把自己照顾好。",
     "过度付出导致空虚，或创造力卡在依赖里。", "金星"),
    (4, "皇帝", "The Emperor", "秩序·权威·结构", "需要规则与边界，用制度而不是情绪解决问题。",
     "僵化控制，或用强硬掩饰不安全感。", "白羊座"),
    (5, "教皇", "The Hierophant", "传承·规矩·指引", "沿着已被验证的路径走，找一位过来人问问。",
     "为反对而反对，或被教条绑住不敢越界。", "金牛座"),
    (6, "恋人", "The Lovers", "选择·结合·价值观", "面临真实的选择，选那个与你的价值观对齐的。",
     "摇摆不定、关系失衡，或把决定权交给别人。", "双子座"),
    (7, "战车", "The Chariot", "前进·掌控·意志", "方向已定，靠自律和专注把事推过去，别分心。",
     "发力过猛，或方向还没定就猛踩油门。", "巨蟹座"),
    (8, "力量", "Strength", "柔韧·耐心·勇气", "真正的强是温柔而持久，用耐心驯服那头猛兽。",
     "自我怀疑，或用蛮力对抗本该顺应的事。", "狮子座"),
    (9, "隐者", "The Hermit", "独处·内省·指引", "需要一段退出来想清楚的时间，答案在安静里。",
     "逃避人群变成封闭，或明知该静却不停外求。", "处女座"),
    (10, "命运之轮", "Wheel of Fortune", "转机·周期·顺势", "局势正在转，抓住窗口期，顺势比硬拼划算。",
     "抗拒变化，或被反复无常的运气推着走。", "木星"),
    (11, "正义", "Justice", "公正·权衡·因果", "该算清楚的账要算清，公平的方案才走得远。",
     "偏袒、逃避责任，或纠结于对错而不做决定。", "天秤座"),
    (12, "倒吊人", "The Hanged Man", "暂停·换视角·舍得", "主动停下来换个角度看，暂时的小舍是必要成本。",
     "无意义的拖延，或用牺牲换取道德优越感。", "海王星"),
    (13, "死神", "Death", "终结·转化·断舍离", "一件事必须彻底结束，新的才进得来，别拖着旧壳。",
     "害怕改变而僵在原地，或结束得太粗暴。", "天蝎座"),
    (14, "节制", "Temperance", "调和·中道·节奏", "把极端调回中间，慢一点混合，比例对了自然成。",
     "失衡、过度，或在两个极端之间反复横跳。", "射手座"),
    (15, "恶魔", "The Devil", "束缚·欲望·执念", "看清那条绑住你的链条其实是自己扣上的。",
     "沉溺与成瘾，或明知有害却反复回头。", "摩羯座"),
    (16, "高塔", "The Tower", "崩塌·顿悟·解放", "旧结构撑不住了，塌掉反而是解脱，别急着重建同样的东西。",
     "硬撑即将倒塌的结构，或把冲击当成世界末日。", "火星"),
    (17, "星星", "The Star", "希望·疗愈·灵感", "最暗的时候已经过去，保持一点信心，慢慢来会好。",
     "信心流失，或把希望寄托在不切实际的地方。", "水瓶座"),
    (18, "月亮", "The Moon", "迷雾·潜意识·不安", "眼前信息不全，别急着下结论，先看清自己的恐惧。",
     "被想象和误会牵着走，或掩饰真正的问题。", "双鱼座"),
    (19, "太阳", "The Sun", "明朗·成功·坦率", "事情在往亮处走，可以大方一点、直接一点。",
     "过度乐观忽略细节，或用热闹掩盖空洞。", "太阳"),
    (20, "审判", "Judgement", "觉醒·召唤·清算", "一个旧阶段的总结账，听见召唤就别再装没听见。",
     "自我批判过度，或拒绝承认已经到来的转变。", "冥王星"),
    (21, "世界", "The World", "完成·整合·收官", "一件事圆满收尾，把经验收进身体里再出发。",
     "差临门一脚却松懈，或结而不收、故事讲不完。", "土星"),
]

_MINOR_NUMBERS = [
    (1, "Ace", "全新开端·种子·机会", "一个新的起点已经在手上，值得认真接住。",
     "机会被错过，或开了头却没有后续。"),
    (2, "Two", "抉择·平衡·初步互动", "两股力量需要调和，先定标准再选。",
     "左右摇摆，或因为怕得罪人而不做选择。"),
    (3, "Three", "成长·协作·初步成果", "第一阶段的成果显现，找对人一起做会更好。",
     "配合失衡、节奏混乱，或第三方的干扰。"),
    (4, "Four", "稳定·框架·休整", "把基础打牢，稳定本身就是这一阶段的成果。",
     "过度保守变成停滞，或安全感来自紧抓不放。"),
    (5, "Five", "冲突·失落·考验", "有摩擦或损失，但它是真实的反馈，别浪费。",
     "陷在情绪里出不来，或反复消耗同一件事。"),
    (6, "Six", "过渡·互助·回味", "最难的阶段在收尾，试着接受或给予帮助。",
     "迈不过去，或把过渡期当成终点。"),
    (7, "Seven", "评估·坚持·策略", "需要复盘与策略，别只靠惯性往前冲。",
     "努力方向错了，或被细节拖住看不到全貌。"),
    (8, "Eight", "推进·熟练·速率", "保持节奏，把事一件件推完，量变正在积累。",
     "忙乱无章，或急于求成导致返工。"),
    (9, "Nine", "接近完成·独自·余味", "离目标很近了，最后一步靠自己走完。",
     "功亏一篑，或一个人在焦虑里空转。"),
    (10, "Ten", "完成·负担·交接", "一个阶段到了终点，把结果和负担一起交接出去。",
     "背得太多不肯放下，或结束得拖泥带水。"),
]

_COURT = [
    ("侍从", "Page", "消息·学习·试探", "有新消息或新兴趣，带着好奇心去试就好。",
     "消息延迟、三分钟热度，或准备永远做不完。"),
    ("骑士", "Knight", "行动·出发·冲劲", "该动起来了，速度与热情是你现在的优势。",
     "鲁莽、半途而废，或只有气势没有方向。"),
    ("王后", "Queen", "成熟·包容·内化", "用成熟的方式处理，你已经具备所需的能力。",
     "过度情绪化或过度控制，把关怀变成束缚。"),
    ("国王", "King", "掌控·权威·定局", "以主导者姿态拍板，用经验把局面稳住。",
     "专断、冷漠，或过度依赖身份而非判断。"),
]

_MINOR_FOCUS = {
    "权杖": "事业、行动力与热情",
    "圣杯": "感情、关系与内心",
    "宝剑": "思维、沟通与决定",
    "星币": "金钱、工作与身体",
}


def _minor_cards():
    deck = []
    for suit, suit_en, element, glyph in SUITS:
        for number, name_en, keywords, upright, reversed_text in _MINOR_NUMBERS:
            deck.append({
                "id": f"{suit_en.lower()}-{number}",
                "arcana": "minor", "suit": suit, "suit_en": suit_en,
                "glyph": glyph, "element": element, "number": number,
                "name": f"{suit}{number}", "name_en": f"{name_en} of {suit_en}",
                "keywords": keywords,
                "upright": f"（{_MINOR_FOCUS[suit]}）{upright}",
                "reversed_text": f"（{_MINOR_FOCUS[suit]}）{reversed_text}",
                "roman": "", "astrology": element,
            })
        for title, title_en, keywords, upright, reversed_text in _COURT:
            deck.append({
                "id": f"{suit_en.lower()}-{title_en.lower()}",
                "arcana": "minor", "suit": suit, "suit_en": suit_en,
                "glyph": glyph, "element": element, "number": None,
                "name": f"{suit}{title}", "name_en": f"{title_en} of {suit_en}",
                "keywords": keywords,
                "upright": f"（{_MINOR_FOCUS[suit]}）{upright}",
                "reversed_text": f"（{_MINOR_FOCUS[suit]}）{reversed_text}",
                "roman": "", "astrology": element,
            })
    return deck


def full_deck():
    """返回 78 张牌的基础数据（不含正逆位）。"""
    deck = []
    for number, name, name_en, keywords, upright, reversed_text, astrology in MAJOR_ARCANA:
        deck.append({
            "id": f"major-{number}",
            "arcana": "major", "suit": "大阿卡纳", "suit_en": "Major Arcana",
            "glyph": "✶", "element": "", "number": number,
            "name": name, "name_en": name_en, "keywords": keywords,
            "upright": upright, "reversed_text": reversed_text,
            "roman": ROMAN[number], "astrology": astrology,
        })
    deck.extend(_minor_cards())
    return deck


def deck_size():
    return len(full_deck())


SPREADS = {
    "celtic": {
        "label": "凯尔特十字（10 张 · 全面）",
        "positions": [
            ("now", "现状", "当下处境的核心"),
            ("challenge", "阻碍/助力", "横在面前的那股力量"),
            ("root", "根源", "事情由何而起"),
            ("past", "过去", "已经过去却仍在影响的"),
            ("crown", "意识目标", "你期望的方向"),
            ("future", "近期发展", "接下来会浮现的"),
            ("self", "自我态度", "你在这件事里的位置"),
            ("environment", "环境/他人", "外界如何看待"),
            ("hopes", "希望与担忧", "心里真正在意什么"),
            ("outcome", "结果", "顺此发展下去的落点"),
        ],
    },
    "three": {
        "label": "时间之流（3 张 · 过去/现在/未来）",
        "positions": [
            ("past", "过去", "已经发生并仍在影响的"),
            ("now", "现在", "当下的核心处境"),
            ("future", "未来", "顺此发展下去的趋势"),
        ],
    },
    "five": {
        "label": "五芒十字（5 张 · 事态剖析）",
        "positions": [
            ("now", "现状", "事情现在的样子"),
            ("challenge", "阻碍", "卡住的地方"),
            ("root", "根源", "深层原因"),
            ("advice", "建议", "可以怎么做"),
            ("outcome", "结果", "可能的落点"),
        ],
    },
    "love": {
        "label": "两性关系（6 张）",
        "positions": [
            ("self", "你的位置", "你在这段关系里的状态"),
            ("other", "对方位置", "对方的状态"),
            ("relation", "关系现状", "两人之间正在发生什么"),
            ("challenge", "阻碍", "卡住这段关系的因素"),
            ("advice", "建议", "接下来可以怎么做"),
            ("outcome", "走向", "顺此发展下去的趋势"),
        ],
    },
    "career": {
        "label": "事业抉择（5 张）",
        "positions": [
            ("now", "现状", "当前工作状态"),
            ("strength", "优势", "你手里最有用的牌"),
            ("challenge", "阻碍", "外部或内部的阻力"),
            ("advice", "行动", "下一步最该做的"),
            ("outcome", "结果", "半年内的走势"),
        ],
    },
    "single": {
        "label": "每日一牌（1 张）",
        "positions": [("now", "今日启示", "今天最该留意的一件事")],
    },
}


def spread_keys():
    return list(SPREADS.keys())


def draw(spread_key, seed=None, allow_reversed=True):
    """洗牌抽牌，返回牌阵结果。"""
    spread = SPREADS.get(spread_key) or SPREADS["three"]
    rng = random.Random(seed)

    deck = full_deck()
    rng.shuffle(deck)
    picked = deck[:len(spread["positions"])]

    cards = []
    for card, (key, label, hint) in zip(picked, spread["positions"]):
        is_reversed = bool(allow_reversed and rng.random() < 0.35)
        item = dict(card)
        item.update({
            "key": key,
            "position": label,
            "position_hint": hint,
            "reversed": is_reversed,
            "orientation": "逆位" if is_reversed else "正位",
            "meaning": card["reversed_text"] if is_reversed else card["upright"],
        })
        cards.append(item)

    major_count = sum(1 for card in cards if card["arcana"] == "major")
    reversed_count = sum(1 for card in cards if card["reversed"])

    return {
        "spread": spread_key,
        "spread_label": spread["label"],
        "seed": seed,
        "allow_reversed": allow_reversed,
        "cards": cards,
        "stats": {
            "major_count": major_count,
            "minor_count": len(cards) - major_count,
            "reversed_count": reversed_count,
            "deck_size": deck_size(),
        },
    }


def summarize(result):
    """牌阵的文字速览，便于复制与保存。"""
    if not result:
        return ""
    lines = [f"牌阵：{result['spread_label']}"]
    for index, card in enumerate(result["cards"], 1):
        lines.append(f"{index}. [{card['position']}] {card['name']}（{card['orientation']}）"
                     f" — {card['keywords']}")
    return "\n".join(lines)


def randomize_cards():
    """用于「盲抽」模式：返回打乱后的牌堆（供手动逐张翻开）。"""
    rng = random.Random()
    deck = full_deck()
    rng.shuffle(deck)
    return deck
