"""周易筮法页面。"""
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .. import deepseek, yijing
from ..prompts import yijing_messages
from ..workers import TaskWorker
from .ai import AiRunner, render_structured
from .theme import CINNABAR, GOLD, TEXT, TEXT_DIM

METHODS = [
    ("大衍蓍草（随机）", "stalks"),
    ("铜钱六摇", "coins"),
    ("依此刻起卦", "now"),
    ("依指定时刻起卦", "datetime"),
    ("手动输入爻值", "manual"),
]

LINE_LABELS = ["上爻", "五爻", "四爻", "三爻", "二爻", "初爻"]


class YijingView(QWidget):
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
        self.splitter.addWidget(self._build_result_area())
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

        title = QLabel("起卦")
        title.setObjectName("section")
        layout.addWidget(title)

        self.question_edit = QLineEdit()
        self.question_edit.setPlaceholderText("所占何事（可留空）")
        layout.addWidget(self._row("所问之事", self.question_edit))

        self.method_combo = QComboBox()
        for label, value in METHODS:
            self.method_combo.addItem(label, value)
        self.method_combo.currentIndexChanged.connect(self._sync_method)
        layout.addWidget(self._row("起卦方式", self.method_combo))

        self.datetime_edit = QDateEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd")
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_widget = self._row("日期", self.datetime_edit)
        layout.addWidget(self.datetime_widget)

        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(QDateTime.currentDateTime().time().hour())
        self.hour_widget = self._row("时辰（0-23）", self.hour_spin)
        layout.addWidget(self.hour_widget)

        self.manual_widget = QWidget()
        manual_layout = QGridLayout(self.manual_widget)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(6)
        self.line_spins = []
        for index in range(6):
            label = QLabel(LINE_LABELS[index])
            label.setObjectName("hint")
            spin = QSpinBox()
            spin.setRange(6, 9)
            spin.setValue(7)
            spin.setSuffix("")
            self.line_spins.append(spin)
            manual_layout.addWidget(label, 5 - index, 0)
            manual_layout.addWidget(spin, 5 - index, 1)
        note = QLabel("6=老阴 7=少阳 8=少阴 9=老阳")
        note.setObjectName("hint")
        manual_layout.addWidget(note, 6, 0, 1, 2)
        layout.addWidget(self.manual_widget)

        self.cast_button = QPushButton("起卦")
        self.cast_button.setObjectName("primary")
        self.cast_button.clicked.connect(self.cast)
        layout.addWidget(self.cast_button)

        hint = QLabel("大衍筮法模拟古法十八变；铜钱法按三枚钱币概率模型；两者均由本地计算。")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addSpacing(8)
        ai_title = QLabel("AI 解读")
        ai_title.setObjectName("section")
        layout.addWidget(ai_title)

        self.ai_button = QPushButton("请模型解卦")
        self.ai_button.clicked.connect(self.run_ai)
        layout.addWidget(self.ai_button)

        layout.addStretch(1)
        self._sync_method()
        return panel

    def _sync_method(self):
        method = self.method_combo.currentData()
        self.datetime_widget.setVisible(method == "datetime")
        self.hour_widget.setVisible(method == "datetime")
        self.manual_widget.setVisible(method == "manual")

    def _build_result_area(self):
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.head = QLabel("尚未起卦")
        self.head.setObjectName("hint")
        self.head.setWordWrap(True)
        layout.addWidget(self.head)

        self.gua_view = QTextBrowser()
        self.gua_view.setMaximumHeight(230)
        layout.addWidget(self.gua_view)

        self.tabs = QTabWidget()
        self.texts_view = QTextBrowser()
        self.najia_ben = QTableWidget(6, 5)
        self.najia_zhi = QTableWidget(6, 5)
        for table in (self.najia_ben, self.najia_zhi):
            table.setHorizontalHeaderLabels(["爻位", "纳甲", "五行", "六亲", "六兽"])
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.verticalHeader().setVisible(False)
            table.setFixedHeight(220)
        self.tabs.addTab(self.texts_view, "卦爻辞")
        self.tabs.addTab(self.najia_ben, "本卦纳甲")
        self.tabs.addTab(self.najia_zhi, "之卦纳甲")
        layout.addWidget(self.tabs, 1)
        return area

    def _build_reading_area(self):
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        caption = QLabel("解卦")
        caption.setObjectName("section")
        layout.addWidget(caption)

        self.browser = QTextBrowser()
        self.browser.setHtml(f"<div style='color:{TEXT_DIM};padding:16px;'>"
                             "先起卦，再让模型结合卦象与所问之事给出取舍建议。</div>")
        layout.addWidget(self.browser, 1)
        return area

    # ---------- 起卦 ----------
    def _task(self):
        method = self.method_combo.currentData()
        if method == "stalks":
            return yijing.stalks
        if method == "coins":
            return yijing.coins
        if method == "now":
            return yijing.qigua_now
        if method == "datetime":
            selected = self.datetime_edit.date()
            return lambda: yijing.by_datetime(selected.year(), selected.month(), selected.day(), self.hour_spin.value())
        lines = "".join(str(spin.value()) for spin in reversed(self.line_spins))
        return lambda: yijing.manual(lines)

    def cast(self):
        self.cast_button.setEnabled(False)
        self.status.showMessage("正在起卦…")
        self.worker = TaskWorker(self._task(), parent=self)
        self.worker.finished.connect(self._on_result)
        self.worker.failed.connect(self._on_error)
        self.worker.start()

    def _on_error(self, message):
        self.cast_button.setEnabled(True)
        self.status.showMessage("起卦失败")
        QMessageBox.warning(self, "起卦失败", message)

    def _on_result(self, raw):
        self.cast_button.setEnabled(True)
        self.result = yijing.normalize(raw)
        self._render()
        self.status.showMessage("起卦完成")

    def _render(self):
        result = self.result
        if not result:
            return

        ben = result.get("ben_gua", "") or "—"
        zhi = result.get("zhi_gua", "") or "—"
        moving = [d for d in yijing.line_detail(result.get("lines", "")) if d["moving"]]
        head_bits = [f"本卦 {ben}", f"之卦 {zhi}", f"动爻 {len(moving)} 根"]
        if result.get("date"):
            head_bits.insert(0, result["date"])
        self.head.setText("　|　".join(head_bits))

        rows = []
        najia = result.get("najia", {}) or {}
        ben_block = najia.get("本卦", {})
        for detail in reversed(yijing.line_detail(result.get("lines", ""))):
            value = detail["value"]
            name = LINE_LABELS[5 - detail["index"]]
            color = CINNABAR if detail["moving"] else TEXT
            mark = "●" if detail["moving"] else ""
            rows.append(
                f"<div style='margin:2px 0;'>"
                f"<span style='color:{TEXT_DIM};display:inline-block;width:48px;'>{name}</span>"
                f"<span style='font-family:monospace;color:{color};letter-spacing:2px;'>{detail['glyph']}</span>"
                f"<span style='color:{TEXT_DIM};font-size:12px;'> {detail['name']} {mark}</span></div>"
            )
        self.gua_view.setHtml(
            f"<div style='padding:10px 14px;'><div style='color:{GOLD};font-size:15px;margin-bottom:8px;'>"
            f"{ben} 之 {zhi}</div>" + "".join(rows) + "</div>"
        )

        texts = result.get("texts", {}) or {}
        advice = result.get("advice", []) or []
        text_html = "".join(
            f"<p style='margin:6px 0;line-height:1.8;'><span style='color:{GOLD};'>{key}</span>：{value}</p>"
            for key, value in texts.items()
        )
        if advice:
            text_html += "<p style='margin:10px 0;line-height:1.8;color:#9a958c;'>" + "；".join(advice) + "</p>"
        self.texts_view.setHtml(text_html or f"<div style='color:{TEXT_DIM};padding:12px;'>暂无卦爻辞</div>")

        self._fill_najia(self.najia_ben, najia.get("本卦", {}))
        self._fill_najia(self.najia_zhi, najia.get("之卦", {}))
        if not ben_block:
            self.tabs.setTabEnabled(1, False)
            self.tabs.setTabEnabled(2, False)
        else:
            self.tabs.setTabEnabled(1, True)
            self.tabs.setTabEnabled(2, True)

    def _fill_najia(self, table, block):
        if not block:
            table.setRowCount(0)
            return
        table.setRowCount(6)
        najia = block.get("najia", [])
        wuxing = block.get("wuxing", [])
        liuqin = block.get("liuqin", [])
        mons = block.get("mons", [])
        for index in range(6):
            values = [
                LINE_LABELS[index],
                najia[index] if index < len(najia) else "",
                wuxing[index] if index < len(wuxing) else "",
                liuqin[index] if index < len(liuqin) else "",
                mons[index] if index < len(mons) else "",
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignCenter)
                table.setItem(index, col, cell)
        table.resizeColumnsToContents()

    # ---------- AI ----------
    def run_ai(self):
        if not self.result:
            QMessageBox.information(self, "先起卦", "请先起卦，再做解读。")
            return

        def on_success(content):
            data = deepseek.extract_json(content)
            render_structured(self.browser, data)

        self.ai.run(yijing_messages(self.result, self.question_edit.text()), on_success, "解卦")
