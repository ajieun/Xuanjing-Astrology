"""AI 解读提示词：把确定性计算结果交给模型做「翻译」。

原则：排盘与格局判定由本地规则引擎完成，模型只负责把象数语言翻译成人话。
"""
import datetime
import json

from . import knowledge

_PERSONA = """你是一位精通中国传统命理的咨询顾问，融会紫微斗数（三合派、中州派）、
周易象数、道家阴阳五行思想。你的表达风格：

- 像朋友聊天，不像老师讲课；有主见，敢下判断，不说模棱两可的话。
- 先用日常类比把术语翻译成人话，再讲它对现实生活的实际影响。
- 先看到格局的积极面，再温和指出需要注意的地方。
- 严禁预言死亡、严禁制造恐惧、严禁替代用户做决策。
  用「这个格局倾向于……」而不是「你一定会……」。
- 命盘显示可能性，行动决定现实；涉及健康、法律、投资时提醒咨询专业人士。
- 全文使用简体中文。"""


def _now_info():
    """每次调用都重新读取系统时间，绝不缓存、绝不写死。"""
    moment = datetime.datetime.now()
    lunar_text = ""
    ganzhi = ""
    next_ganzhi = ""
    try:
        from lunar_python import Solar

        lunar = Solar.fromYmdHms(
            moment.year, moment.month, moment.day,
            moment.hour, moment.minute, moment.second,
        ).getLunar()
        ganzhi = lunar.getYearInGanZhi()
        lunar_text = f"{ganzhi}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}"
        next_ganzhi = Solar.fromYmd(moment.year + 1, 6, 1).getLunar().getYearInGanZhi()
    except Exception:  # noqa: BLE001 - 历法库异常时退回纯公历
        pass
    return moment, lunar_text, ganzhi, next_ganzhi


def _today_block():
    """把请求当刻的真实时间写进提示词，避免模型拿训练数据里的旧年份当「今年」。"""
    moment, lunar_text, ganzhi, next_ganzhi = _now_info()
    weekday = "一二三四五六日"[moment.weekday()]
    lines = [
        "时间基准（每次请求实时获取，必须遵守）：",
        f"- 现在是 {moment.year} 年 {moment.month} 月 {moment.day} 日 "
        f"{moment.hour:02d}:{moment.minute:02d}（星期{weekday}，Asia/Shanghai）。",
    ]
    if lunar_text:
        lines.append(f"- 当前农历：{lunar_text}；当前流年：{ganzhi}年（{moment.year}）。")
        if next_ganzhi:
            lines.append(f"- 下一个流年：{next_ganzhi}年（{moment.year + 1}）。")
    lines.append(
        f"- 「今年」「明年」「近两年」「当前流年」「未来几年」一律以此为基准，正文里写明确年份。"
    )
    lines.append(
        f"- 训练数据里的旧年份已经过期：早于 {moment.year} 年的年份只能是过去，不能当作未来或当下。"
    )
    return "\n".join(lines)


def _time_hint():
    """放在 user 消息末尾的一句话时间锚点（离模型最近，遵守率最高）。"""
    moment, _, ganzhi, _ = _now_info()
    suffix = f"，当前流年 {ganzhi}年" if ganzhi else ""
    return (
        f"【时间锚点】今天实时时间为 {moment.year} 年 {moment.month} 月 {moment.day} 日"
        f" {moment.hour:02d}:{moment.minute:02d}{suffix}。"
        f"凡涉及「今年/明年/未来几年」的表述，都必须以此推算，"
        f"禁止把 {moment.year - 1} 年及更早的年份当作当下。"
    )


def _base():
    return _PERSONA + "\n\n" + _today_block()


_COMMON_RULES = """输出要求：
- 只输出一个 JSON 对象：第一个字符必须是 {，最后一个字符必须是 }。
- 不要出现 ``` 代码块围栏，不要有任何解释性前后缀。
- JSON 必须能被 Python json.loads 直接解析。
- 所有正文类字段（body / reading / overall / advice / cautions / actions / timing 等）只写自然语言；
  严禁在这些字段里嵌套或粘贴 JSON、键值对、大括号结构、代码块，也不要重复整份结构。
- 正文需要强调时只允许 <strong> <em> <br> <span class='warn'> <span class='good'> 这些简单标签。
- 参考资料里可能出现繁体字，输出时一律转成简体中文。"""


def _compact_chart(chart_data):
    payload = json.loads(json.dumps(chart_data, ensure_ascii=False))
    travel = payload.get("time_travel_analysis") or {}
    travel.pop("full_time_log", None)
    for palace in payload.get("palaces", []):
        palace.pop("adjective_stars", None)
    return json.dumps(payload, ensure_ascii=False)


def ziwei_messages(chart_data, focus="", extra_note=""):
    guide = dict(knowledge.articles()).get("紫微 · 解读风格指南", "")
    stars = dict(knowledge.articles()).get("紫微 · 十四主星与六吉六煞", "")
    sihua = dict(knowledge.articles()).get("紫微 · 四化飞星参考", "")

    focus_text = focus.strip() or "全面解读（命盘底色、事业、财运、感情、当前大限）"
    system = "\n\n".join([
        _base(),
        "下面是本地典籍，作为你的取象与措辞依据：",
        "### 解读风格指南\n" + (guide or "（略）"),
        "### 星曜参考\n" + (stars or "（略）"),
        "### 四化飞星参考\n" + (sihua or "（略）"),
        _COMMON_RULES,
        """JSON 结构：
{
  "current_decadal_display": "当前大限展示文字，如「辰宫·天机·天梁」",
  "cards": [
    {
      "title": "章节标题",
      "badge": "主星或宫位标签",
      "full": true,
      "highlight": true,
      "body": "正文，可用 <strong>强调</strong> <em>金色</em> <span class='warn'>提醒</span> <span class='good'>利好</span> <br> 换行",
      "probabilities": [{"label": "推算置信度", "pct": 70}]
    }
  ],
  "calibration_questions": [{"text": "问题", "hint": "提示"}]
}

章节安排：命盘底色、事业、财运、感情、当前大限（共 5 章）。
第 5 章之外不要额外写「宏观格局仪表盘」和「时空压力审计」两章，界面已由规则引擎渲染。
把 gezhi_analysis 的格局判定当作解读基调，把 time_travel_analysis 的高压宫位自然写进流年提示。
每章 2-4 段，不要写成教科书。calibration_questions 给 3-5 个用于校准的问题。""",
    ])

    target_year = (chart_data.get("time_travel_analysis") or {}).get("target_year")
    target_year = target_year or datetime.date.today().year

    user = "\n\n".join([
        f"本次解读重点：{focus_text}",
        f"本次流年基准：{target_year} 年（流年压力与应期均按这一年推算，不要换成别的年份）",
        "排盘数据（本地规则引擎确定性计算，请以此为准，不要自行改盘）：",
        "```json\n" + _compact_chart(chart_data) + "\n```",
        extra_note.strip() or "（无补充信息）",
        _time_hint(),
    ])

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def yijing_messages(result, question=""):
    system = "\n\n".join([
        _base(),
        """你现在做的是周易筮法解读。依据朱熹《易学启蒙》考变占：
0 动爻看本卦彖辞；1 爻动看本卦动爻辞；2 爻动兼看两动爻辞（上爻为主）；
3 爻动参本卦与之卦彖辞（初爻变主贞，二爻起变主悔）；
4 爻动看之卦两静爻（下爻为主）；5 爻动看之卦独静爻；6 爻皆变乾坤看二用、余卦看之卦彖辞。
可以引用卦辞、爻辞、彖辞、象辞，也可以引入道家阴阳消长的视角，
但必须落回用户问的具体事情上，给出可执行的取舍建议。""",
        _COMMON_RULES,
        """JSON 结构：
{
  "overall": "总断：一段话给出核心判断（简体中文，可含 1-2 个 **加粗** 关键词）",
  "lines_reading": ["由初爻到上爻，逐爻一句白话解释（只解释有信息量的爻）"],
  "actions": ["宜做的 2-4 条具体行动"],
  "cautions": ["需要留意的 2-4 条风险或时机"],
  "timing": "时机判断：一句话说明当前是「可为」「守成」还是「待时」"
}""",
    ])

    user = "\n\n".join([
        f"所占之事：{question.strip() or '（未写明具体问题，作整体近况占）'}",
        "起卦结果（本地筮法引擎计算）：",
        "```json\n" + json.dumps(result, ensure_ascii=False) + "\n```",
        _time_hint(),
    ])
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def tarot_messages(result, question="", focus=""):
    system = "\n\n".join([
        _base(),
        """你现在做的是塔罗牌解读（韦特体系，含正逆位）。要点：

- 你是在跟一个朋友喝咖啡时解牌，不是在做卡牌说明书。不要逐张复述牌义。
- 先把牌阵读成一个完整的故事：这些牌凑在一起，说明当事人正处在什么样的局面里。
- 逆位不是「坏牌」，而是能量受阻、内化、过度或尚未到位，要说清是哪一种。
- 大阿卡纳多说明是人生阶段的议题，小阿卡纳多说明是日常具体的事件层面；
  同一牌组里出现多张同花色/同元素，要点出来，那是这件事的主战场。
- 每张牌的解读必须回扣到牌位（现状/阻碍/根源/建议/结果……）上，
  说「这张牌在这个位置上意味着什么」，而不是「这张牌的意思是什么」。
- 严禁预言死亡、疾病与灾祸，严禁制造恐惧；给出可执行的取舍与节奏建议。""",
        _COMMON_RULES,
        """JSON 结构：
{
  "overall": "总断：把牌阵串成一段完整的判断（简体中文，可含 1-2 个 **加粗** 关键词）",
  "cards_reading": [
    {"position": "牌位名", "card": "牌名（含正逆位）", "reading": "白话解读，2-3 句，必须扣住牌位"}
  ],
  "sections": [{"title": "牌阵里的主线", "body": "可含 <strong>强调</strong> 的一段文字"}],
  "actions": ["2-4 条接下来可以做的具体行动"],
  "cautions": ["2-4 条需要留意或避免的"],
  "timing": "时机判断：一句话说明现在是「可为」「守成」还是「待时」"
}

cards_reading 必须覆盖牌阵里的每一张牌，顺序与给定数据一致。""",
    ])

    user = "\n\n".join([
        f"所占之事：{question.strip() or '（未写明具体问题，作整体近况占）'}",
        f"解读重点：{focus.strip() or '整体走势'}",
        "牌阵数据（本地洗牌抽取，牌义以给定内容为准）：",
        "```json\n" + json.dumps(result, ensure_ascii=False) + "\n```",
        _time_hint(),
    ])
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def daoyin_messages(bazi, focus=""):
    system = "\n\n".join([
        _base(),
        """你现在做的是道家术数视角的四柱解读：以阴阳五行生克制化、三元九运当令之气、
建除十二神的宜忌为骨架，用《道德经》《清静经》的处世智慧来收束建议。
观点要明确，但要落到具体的生活节奏、用神取舍与一两年的时机判断上。""",
        _COMMON_RULES,
        """JSON 结构：
{
  "overall": "命局总断：日主强弱、格局倾向、一句话概括",
  "sections": [
    {"title": "五行与用神", "body": "正文"},
    {"title": "事业与时机", "body": "正文"},
    {"title": "财运", "body": "正文"},
    {"title": "身心与修持", "body": "正文"}
  ],
  "advice": ["2-4 条可执行建议"]
}""",
    ])

    user = "\n\n".join([
        f"解读重点：{focus.strip() or '命局与近两年时机'}",
        "四柱与术数数据（本地历法库计算）：",
        "```json\n" + json.dumps(bazi, ensure_ascii=False, default=str) + "\n```",
        _time_hint(),
    ])
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
