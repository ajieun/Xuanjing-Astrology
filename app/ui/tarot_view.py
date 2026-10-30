"""塔罗牌占卜页面。"""
import json
import os
import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .. import deepseek, tarot
from ..prompts import tarot_messages
from ..resources import user_dir
from ..workers import TaskWorker
from .ai import AiRunner, render_structured
from .card_dialog import CARD_H, CARD_W, CardDetailDialog, TarotCardWidget
from .theme import GOLD, TEXT_DIM

FOCUS_ITEMS = ["整体走势", "感情关系", "事业与钱", "抉择与方向", "近期（三个月内）"]


class _CardArea(QScrollArea):
    """自适应列宽的牌面区域。"""

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(14)
        self.grid.setContentsMargins(2, 2, 2, 2)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setWidget(self.container)
        self._cards = []

    def place(self, widgets):
        self._cards = widgets
        self.relayout()

    def relayout(self):
        cards = getattr(self, "_cards", [])
        if not cards:
            return
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        columns = max(1, self.viewport().width() // (CARD_W + 14))
        for index, widget in enumerate(cards):
            self.grid.addWidget(widget, index // columns, index % columns)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self.relayout()


class TarotView(QWidget):
    def __init__(self, settings_getter, status, parent=None):
        super().__init__(parent)
        self.settings_getter = settings_getter
        self.status = status
        self.result = None
        self.worker = None

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)
        root.addWidget(self._build_form(), 0)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self._build_card_area())
        self.splitter.addWidget(self._build_reading_area())
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        root.addWidget(self.splitter, 1)

        self.ai = AiRunner(self, self.browser, status, settings_getter, self.ai_button)

    def _row(self, label, widget):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        caption = QLabel(label)
        caption.setObjectName("hint")
        layout.addWidget(caption)
        layout.addWidget(widget)
        return container

    def _build_form(self):
        panel = QWidget()
        panel.setFixedWidth(268)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("抽牌")
        title.setObjectName("section")
        layout.addWidget(title)

        self.question_edit = QLineEdit()
        self.question_edit.setPlaceholderText("你想问的事（可留空作整体占）")
        layout.addWidget(self._row("问题", self.question_edit))

        self.spread_combo = QComboBox()
        for key in tarot.spread_keys():
            self.spread_combo.addItem(tarot.SPREADS[key]["label"], key)
        self.spread_combo.setCurrentIndex(0)
        layout.addWidget(self._row("牌阵", self.spread_combo))

        self.reversed_check = QCheckBox("启用逆位（约 1/3 概率）")
        self.reversed_check.setChecked(True)
        layout.addWidget(self.reversed_check)

        self.seed_edit = QLineEdit()
        self.seed_edit.setPlaceholderText("留空则随机；填同一值可复现同一副牌")
        layout.addWidget(self._row("随机种子", self.seed_edit))

        self.draw_button = QPushButton("洗牌抽牌")
        self.draw_button.setObjectName("primary")
        self.draw_button.clicked.connect(self.draw)
        layout.addWidget(self.draw_button)

        self.copy_button = QPushButton("复制牌面速览")
        self.copy_button.clicked.connect(self.copy_summary)
        layout.addWidget(self.copy_button)

        self.save_button = QPushButton("保存牌阵 JSON")
        self.save_button.clicked.connect(self.save_result)
        layout.addWidget(self.save_button)

        hint = QLabel("洗牌在本地完成，可用种子复现；牌义为韦特体系通行释义。")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addSpacing(8)
        ai_title = QLabel("AI 解读")
        ai_title.setObjectName("section")
        layout.addWidget(ai_title)

        self.focus_combo = QComboBox()
        self.focus_combo.addItems(FOCUS_ITEMS)
        layout.addWidget(self._row("重点", self.focus_combo))

        self.ai_button = QPushButton("请模型解牌")
        self.ai_button.clicked.connect(self.run_ai)
        layout.addWidget(self.ai_button)

        layout.addStretch(1)
        return panel

    def _build_card_area(self):
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.head = QLabel("尚未抽牌")
        self.head.setObjectName("hint")
        self.head.setWordWrap(True)
        layout.addWidget(self.head)

        self.card_area = _CardArea()
        layout.addWidget(self.card_area, 1)
        return area

    def _build_reading_area(self):
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        caption = QLabel("解牌")
        caption.setObjectName("section")
        layout.addWidget(caption)

        self.browser = QTextBrowser()
        self.browser.setHtml(f"<div style='color:{TEXT_DIM};padding:16px;'>"
                             "先抽牌，再让模型把牌阵串成一个完整的故事。</div>")
        layout.addWidget(self.browser, 1)
        return area

    # ---------- 抽牌 ----------
    def draw(self):
        seed_text = self.seed_edit.text().strip()
        seed = seed_text if seed_text else f"{time.time_ns()}"
        payload = {
            "spread_key": self.spread_combo.currentData(),
            "seed": seed,
            "allow_reversed": self.reversed_check.isChecked(),
        }
        self.draw_button.setEnabled(False)
        self.status.showMessage("正在洗牌…")
        self.worker = TaskWorker(tarot.draw, parent=self, **payload)
        self.worker.finished.connect(self._on_result)
        self.worker.failed.connect(self._on_error)
        self.worker.start()

    def _on_error(self, message):
        self.draw_button.setEnabled(True)
        self.status.showMessage("抽牌失败")
        QMessageBox.warning(self, "抽牌失败", message)

    def _on_result(self, result):
        self.draw_button.setEnabled(True)
        self.result = result
        self._render()
        self.status.showMessage("抽牌完成")

    def _render(self):
        result = self.result
        if not result:
            return

        stats = result.get("stats", {})
        self.head.setText("　|　".join([
            result.get("spread_label", ""),
            f"大阿卡纳 {stats.get('major_count', 0)} 张 / 小阿卡纳 {stats.get('minor_count', 0)} 张",
            f"逆位 {stats.get('reversed_count', 0)} 张",
            f"种子 {result.get('seed', '')}",
        ]))

        widgets = []
        for index, card in enumerate(result.get("cards", []), 1):
            widget = TarotCardWidget(card, index)
            widget.mouseReleaseEvent = lambda _event, c=card: self._show_detail(c)  # noqa: E731
            widgets.append(widget)
        self.card_area.place(widgets)

    def _show_detail(self, card):
        CardDetailDialog(card, self).exec()

    def copy_summary(self):
        if not self.result:
            QMessageBox.information(self, "尚未抽牌", "请先抽牌。")
            return
        QApplication.clipboard().setText(tarot.summarize(self.result))
        self.status.showMessage("牌面速览已复制到剪贴板")

    def save_result(self):
        if not self.result:
            QMessageBox.information(self, "尚未抽牌", "请先抽牌。")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存牌阵", os.path.join(user_dir(), "tarot.json"), "JSON 文件 (*.json)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.result, handle, ensure_ascii=False, indent=2)
        self.status.showMessage(f"已保存：{path}")

    # ---------- AI ----------
    def run_ai(self):
        if not self.result:
            QMessageBox.information(self, "先抽牌", "请先洗牌抽牌，再做解读。")
            return

        def on_success(content):
            render_structured(self.browser, deepseek.extract_json(content),
                              "overall", "cards_reading")

        self.ai.run(
            tarot_messages(self.result, self.question_edit.text(), self.focus_combo.currentText()),
            on_success,
            "塔罗解牌",
        )
