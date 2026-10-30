"""十二宫宫位卡片。"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from .theme import CINNABAR, GOLD, JADE, TEXT, TEXT_DIM


class PalaceCard(QFrame):
    clicked = Signal(dict)

    def __init__(self, palace, soul_branch="", limit_branch="", parent=None):
        super().__init__(parent)
        self.palace = palace
        self.setCursor(Qt.PointingHandCursor)

        branch = palace.get("earthly_branch", "")
        is_soul = branch == soul_branch
        is_limit = branch and branch == limit_branch
        is_empty = bool(palace.get("is_empty_palace", False))

        if is_soul:
            self.setObjectName("cardSoul")
        elif is_limit:
            self.setObjectName("cardLimit")
        elif is_empty:
            self.setObjectName("cardEmpty")
        else:
            self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 8, 9, 8)
        layout.setSpacing(3)

        header = QLabel(f"{palace.get('name', '')} · {branch}")
        header.setStyleSheet(f"font-size:12px;color:{GOLD if is_soul else TEXT_DIM};letter-spacing:1px;")
        layout.addWidget(header)

        self.stars = QLabel(self._star_text(palace))
        self.stars.setStyleSheet(f"font-size:14px;color:{TEXT};line-height:1.5;")
        self.stars.setWordWrap(True)
        layout.addWidget(self.stars)

        tags = self._tag_text(palace, is_soul, is_limit)
        if tags:
            tag = QLabel(tags)
            tag.setStyleSheet(f"font-size:11px;color:{TEXT_DIM};")
            tag.setWordWrap(True)
            layout.addWidget(tag)

        layout.addStretch(1)

    def _star_text(self, palace):
        if palace.get("is_empty_palace"):
            borrowed = list(palace.get("borrowed_major_stars", [])) + list(palace.get("borrowed_minor_stars", []))
            coef = palace.get("energy_coefficient", 0.7)
            color = CINNABAR if coef == 0.5 else GOLD
            names = " ".join(borrowed) if borrowed else "空宫"
            return f"<span style='color:{JADE};font-style:italic;'>{names}</span><br><span style='color:{color};font-size:11px;'>借星 能量×{coef}</span>"
        major = palace.get("major_stars", []) or []
        minor = palace.get("minor_stars", []) or []
        mutagens = {m["star"]: m["mutagen"] for m in palace.get("mutagens", [])}

        major_html = []
        for star in major:
            mut = mutagens.get(star)
            if mut:
                mark = "化忌" if mut == "忌" else f"化{mut}"
                color = CINNABAR if mut == "忌" else GOLD
                major_html.append(f"<span style='color:{TEXT};'>{star}</span><span style='color:{color};font-size:11px;'>{mark}</span>")
            else:
                major_html.append(f"<span style='color:{TEXT};'>{star}</span>")
        minor_html = " ".join(f"<span style='color:{TEXT_DIM};'>{s}</span>" for s in minor)
        text = " ".join(major_html)
        if minor_html:
            text += f"<br>{minor_html}"
        return text or "<span style='color:#5d5a55;'>空宫</span>"

    def _tag_text(self, palace, is_soul, is_limit):
        tags = []
        if is_soul:
            tags.append("命宫")
        if "身宫" in palace.get("tags", []):
            tags.append("身宫")
        if is_limit:
            tags.append("当前大限")
        if palace.get("decadal_range"):
            tags.append(f"{palace['decadal_range']}岁")
        return " · ".join(tags)

    def mouseReleaseEvent(self, event):  # noqa: N802
        self.clicked.emit(self.palace)
        super().mouseReleaseEvent(event)
