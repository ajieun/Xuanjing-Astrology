"""塔罗牌卡片与详情弹窗。"""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QLabel,
    QTextBrowser,
    QVBoxLayout,
)

from .theme import CINNABAR, FONT_SERIF, GOLD, JADE, TEXT, TEXT_DIM

CARD_W = 132
CARD_H = 208

SUIT_COLORS = {
    "权杖": ("#d0654f", "#f0b27a"),
    "圣杯": ("#6fa08a", "#a8d5c2"),
    "宝剑": ("#8d8fa6", "#cfd3e0"),
    "星币": ("#c8a35a", "#f0dca4"),
    "大阿卡纳": ("#4a3f6b", "#a08fd0"),
}


class TarotCardWidget(QFrame):
    """一张塔罗牌：逆位以翻转 180° 呈现。"""

    def __init__(self, card, index, parent=None):
        super().__init__(parent)
        self.card = card
        self.index = index
        self.setFixedSize(CARD_W, CARD_H)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        self.top, self.accent = SUIT_COLORS.get(card.get("suit", "大阿卡纳"), SUIT_COLORS["大阿卡纳"])
        self._build_face()

    def _build_face(self):
        card = self.card
        self.content = QFrame(self)
        self.content.setGeometry(0, 0, CARD_W, CARD_H)
        self.content.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(9, 10, 9, 10)
        layout.setSpacing(2)

        position = QLabel(f"{self.index}. {card.get('position', '')}")
        position.setStyleSheet(f"color:{self.accent};font-size:10px;letter-spacing:1px;")
        position.setAlignment(Qt.AlignCenter)
        layout.addWidget(position)

        glyph = QLabel(card.get("roman") or card.get("glyph", ""))
        glyph.setStyleSheet(f"color:{self.accent};font-size:24px;")
        glyph.setAlignment(Qt.AlignCenter)
        layout.addWidget(glyph)

        name = QLabel(card.get("name", ""))
        name.setStyleSheet(f"color:{TEXT};font-size:14px;font-family:{FONT_SERIF};")
        name.setAlignment(Qt.AlignCenter)
        name.setWordWrap(True)
        layout.addWidget(name)

        orientation = QLabel(f"{card.get('orientation', '')} · {card.get('keywords', '')}")
        orientation.setStyleSheet(f"color:{TEXT_DIM};font-size:9px;line-height:1.3;")
        orientation.setAlignment(Qt.AlignCenter)
        orientation.setWordWrap(True)
        layout.addWidget(orientation)

        meaning = QLabel(card.get("meaning", ""))
        meaning.setStyleSheet(f"color:{TEXT_DIM};font-size:9px;line-height:1.45;")
        meaning.setAlignment(Qt.AlignCenter)
        meaning.setWordWrap(True)
        layout.addWidget(meaning, 1)

        english = QLabel(card.get("name_en", ""))
        english.setStyleSheet("color:#6a665f;font-size:8px;")
        english.setAlignment(Qt.AlignCenter)
        english.setWordWrap(True)
        layout.addWidget(english)

        if card.get("reversed"):
            mark = QLabel("逆　位　↓")
            mark.setStyleSheet(f"color:{CINNABAR};font-size:9px;letter-spacing:2px;")
            mark.setAlignment(Qt.AlignCenter)
            layout.addWidget(mark)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(1, 1, CARD_W - 2, CARD_H - 2), 8, 8)

        accent = QColor(self.top)
        gradient = QLinearGradient(0, 0, 0, CARD_H)
        if self.card.get("reversed"):
            # 逆位：整体色调翻转，强调「倒过来的能量」
            gradient.setColorAt(0.0, QColor("#141318"))
            gradient.setColorAt(1.0, QColor("#241f26"))
        else:
            gradient.setColorAt(0.0, QColor("#1f1e26"))
            gradient.setColorAt(1.0, QColor("#141318"))
        painter.fillPath(path, QBrush(gradient))

        painter.setPen(QPen(accent, 1.4))
        painter.drawPath(path)

        inner = QPainterPath()
        inner.addRoundedRect(QRectF(6, 6, CARD_W - 12, CARD_H - 12), 5, 5)
        painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 60), 1))
        painter.drawPath(inner)

        # 中央水印符号：逆位时旋转 180°，作为「倒置」的视觉提示
        painter.save()
        painter.translate(CARD_W / 2, CARD_H / 2)
        if self.card.get("reversed"):
            painter.rotate(180)
        painter.setPen(QPen(QColor(accent.red(), accent.green(), accent.blue(), 45), 1))
        painter.setFont(QFont("Georgia", 58))
        painter.drawText(QRectF(-CARD_W / 2, -CARD_H / 2, CARD_W, CARD_H), Qt.AlignCenter,
                         self.card.get("roman") or self.card.get("glyph", ""))
        painter.restore()
        painter.end()

        super().paintEvent(event)


class CardDetailDialog(QDialog):
    """单张牌的正逆位完整牌义。"""

    def __init__(self, card, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{card.get('name', '')} · {card.get('orientation', '')}")
        self.setMinimumSize(460, 470)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        base = card.get("roman") or card.get("glyph", "")
        title = QLabel(f"{base}　{card.get('name', '')}　{card.get('name_en', '')}")
        title.setStyleSheet(f"color:{GOLD};font-size:17px;font-family:{FONT_SERIF};")
        layout.addWidget(title)

        meta = QLabel(
            "　|　".join(filter(None, [
                card.get("position", ""),
                card.get("orientation", ""),
                card.get("suit", ""),
                card.get("astrology", ""),
            ]))
        )
        meta.setStyleSheet(f"color:{TEXT_DIM};font-size:12px;")
        layout.addWidget(meta)

        is_reversed = card.get("reversed")
        current_label = QLabel("本次抽到的牌义")
        current_label.setObjectName("section")
        layout.addWidget(current_label)

        current = QTextBrowser()
        accent = CINNABAR if is_reversed else JADE
        current.setHtml(
            f"<div style='font-size:14px;line-height:1.9;'>"
            f"<span style='color:{accent};'>【{card.get('orientation', '')}】</span> "
            f"{card.get('meaning', '')}<br><br>"
            f"<span style='color:{TEXT_DIM};'>关键词：{card.get('keywords', '')}</span></div>"
        )
        current.setMaximumHeight(130)
        layout.addWidget(current)

        other_label = QLabel("另一面的牌义")
        other_label.setObjectName("section")
        layout.addWidget(other_label)

        other = QTextBrowser()
        other_text = card.get("upright", "") if is_reversed else card.get("reversed_text", "")
        other_orientation = "正位" if is_reversed else "逆位"
        other.setHtml(
            f"<div style='font-size:13px;line-height:1.85;color:{TEXT_DIM};'>"
            f"【{other_orientation}】{other_text}</div>"
        )
        layout.addWidget(other, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Close).setText("关闭")
        layout.addWidget(buttons)
