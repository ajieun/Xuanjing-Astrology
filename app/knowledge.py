"""本地典籍与知识库：紫微参考、道家经典片段、周易说明。"""
import os

from .resources import knowledge_dir, load_text

DAOIST_TEXTS = {
    "道德经 · 节选": """# 道德经（节选）

## 第一章
道可道，非常道；名可名，非常名。无名天地之始，有名万物之母。
故常无欲，以观其妙；常有欲，以观其徼。此两者同出而异名，同谓之玄。
玄之又玄，众妙之门。

## 第八章
上善若水。水善利万物而不争，处众人之所恶，故几于道。
居善地，心善渊，与善仁，言善信，正善治，事善能，动善时。
夫唯不争，故无尤。

## 第十六章
致虚极，守静笃。万物并作，吾以观复。
夫物芸芸，各复归其根。归根曰静，静曰复命。复命曰常，知常曰明。

## 第三十三章
知人者智，自知者明。胜人者有力，自胜者强。
知足者富，强行者有志。不失其所者久，死而不亡者寿。

## 第六十四章
其安易持，其未兆易谋，其脆易泮，其微易散。为之于未有，治之于未乱。
合抱之木，生于毫末；九层之台，起于累土；千里之行，始于足下。
""",
    "庄子 · 节选": """# 庄子（节选）

## 逍遥游
北冥有鱼，其名为鲲。鲲之大，不知其几千里也。化而为鸟，其名为鹏。
鹏之背，不知其几千里也；怒而飞，其翼若垂天之云。

## 养生主
吾生也有涯，而知也无涯。以有涯随无涯，殆已！
已而为知者，殆而已矣！为善无近名，为恶无近刑，缘督以为经。

## 大宗师
知天之所为，知人之所为者，至矣。
""",
    "周易 · 系辞（节选）": """# 周易 · 系辞上传（节选）

## 第一章
天尊地卑，乾坤定矣。卑高以陈，贵贱位矣。动静有常，刚柔断矣。
方以类聚，物以群分，吉凶生矣。在天成象，在地成形，变化见矣。

## 大衍之数
大衍之数五十，其用四十有九。分而为二以象两，挂一以象三，
揲之以四以象四时，归奇于扐以象闰。五岁再闰，故再扐而后挂。

## 第十一章
易曰：自天祐之，吉无不利。子曰：祐者，助也。天之所助者，顺也；
人之所助者，信也。履信思乎顺，又以尚贤也。是以自天祐之，吉无不利也。
""",
    "太上感应篇 · 节选": """# 太上感应篇（节选）

太上曰：祸福无门，惟人自召；善恶之报，如影随形。

是以天地有司过之神，依人所犯轻重，以夺人算。算减则贫耗，多逢忧患，
人皆恶之，刑祸随之，吉庆避之，恶星灾之，算尽则死。

夫心起于善，善虽未为，而吉神已随之；或心起于恶，恶虽未为，而凶神已随之。
其有曾行恶事，后自改悔，诸恶莫作，众善奉行，久久必获吉庆，所谓转祸为福也。

> 故吉人语善、视善、行善，一日有三善，三年天必降之福。
> 凶人语恶、视恶、行恶，一日有三恶，三年天必降之祸。
""",
    "阴符经": """# 黄帝阴符经

观天之道，执天之行，尽矣。

天有五贼，见之者昌。五贼在乎心，施行于天。宇宙在乎手，万化生乎身。

天性，人也；人心，机也。立天之道，以定人也。

天发杀机，移星易宿；地发杀机，龙蛇起陆；人发杀机，天地反覆。
天人合发，万化定基。

> 性有巧拙，可以伏藏。九窍之邪，在乎三要，可以动静。
> 火生于木，祸发必克；奸生于国，时动必溃。知之修之，谓之圣人。
""",
    "清静经": """# 太上老君说常清静经

老君曰：大道无形，生育天地；大道无情，运行日月；大道无名，长养万物。

夫人神好清，而心扰之；人心好静，而欲牵之。
常能遣其欲，而心自静；澄其心，而神自清。自然六欲不生，三毒消灭。

> 内观其心，心无其心；外观其形，形无其形；远观其物，物无其物。
> 三者既悟，唯见于空。观空亦空，空无所空；所空既无，无无亦无；
> 无无既无，湛然常寂；寂无所寂，欲岂能生？欲既不生，即是真静。
""",
}


def _read_reference(name):
    path = os.path.join(knowledge_dir(), name)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return f"> 未找到本地典籍：{name}"


def tarot_reference():
    """由本地牌组数据生成的塔罗牌义速查表。"""
    from . import tarot

    lines = ["# 塔罗牌义速查（韦特体系）", ""]
    lines.append("## 大阿卡纳")
    lines.append("")
    lines.append("| 牌 | 关键词 | 正位 | 逆位 |")
    lines.append("|---|---|---|---|")
    for number, name, name_en, keywords, upright, reversed_text, astrology in tarot.MAJOR_ARCANA:
        lines.append(f"| {tarot.ROMAN[number]} {name}（{name_en}） | {keywords} | {upright} | {reversed_text} |")
    lines.append("")

    for suit, suit_en, element, glyph in tarot.SUITS:
        lines.append(f"## {suit} {suit_en}（{element}）— {tarot._MINOR_FOCUS[suit]}")
        lines.append("")
        lines.append("| 牌 | 关键词 | 正位 | 逆位 |")
        lines.append("|---|---|---|---|")
        for card in tarot.full_deck():
            if card["suit"] != suit:
                continue
            lines.append(f"| {card['name']}（{card['name_en']}） | {card['keywords']} "
                         f"| {card['upright']} | {card['reversed_text']} |")
        lines.append("")

    lines.append("## 牌阵")
    lines.append("")
    for key, spread in tarot.SPREADS.items():
        positions = "、".join(f"{name}（{hint}）" for _, name, hint in spread["positions"])
        lines.append(f"- **{spread['label']}**：{positions}")
    return "\n".join(lines)


def articles():
    """返回知识库文章列表 [(标题, markdown 正文)]。"""
    items = [
        ("紫微 · 解读风格指南", _read_reference("interpretation_guide.md")),
        ("紫微 · 十四主星与六吉六煞", _read_reference("stars_reference.md")),
        ("紫微 · 四化飞星参考", _read_reference("four_hua_reference.md")),
        ("塔罗 · 78 张牌义与牌阵", tarot_reference()),
    ]
    for title, body in DAOIST_TEXTS.items():
        items.append((title, body))
    try:
        items.append(("紫微 · 命理解读师 SKILL", load_text("SKILL.md")))
    except OSError:
        pass
    return items


def search(query, items=None):
    keyword = (query or "").strip().lower()
    pool = items or articles()
    if not keyword:
        return pool
    return [(title, body) for title, body in pool
            if keyword in title.lower() or keyword in body.lower()]
