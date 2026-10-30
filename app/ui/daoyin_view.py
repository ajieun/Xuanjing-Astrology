"""道家术数页面：四柱八字、三元九运、建除与二十八宿。"""
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .. import daoyin, deepseek
from ..prompts import daoyin_messages
from ..workers import TaskWorker
from .ai import AiRunner, render_structured
from .theme import GOLD, JADE, TEXT, TEXT_DIM

FOCUS_ITEMS = ["命局与近两年时机", "事业与方向", "财运与取舍", "身心与修持"]

PILLAR_HINTS = {
    "年柱": "祖上与早年环境",
    "月柱": "父母、事业宫、社会舞台",
    "日柱": "自身与配偶（日主为命局核心）",
    "时柱": "晚年、子女与归宿",
}


class DaoyinView(QWidget):
    def __init__(self, settings_getter, status, parent=None):
        super().__init__(parent)
        self.settings_getter = settings_getter
        self.status = status
        self.bazi = None
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

        title = QLabel("生辰")
        title.setObjectName("section")
        layout.addWidget(title)

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        layout.addWidget(self._row("出生时刻", self.datetime_edit))

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女"])
        layout.addWidget(self._row("性别", self.gender_combo))

        self.calc_button = QPushButton("排四柱")
        self.calc_button.setObjectName("primary")
        self.calc_button.clicked.connect(self.calculate)
        layout.addWidget(self.calc_button)

        hint = QLabel("历法换算由本地农历库完成；三元九运与建除按传统规则推算。")
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

        self.ai_button = QPushButton("请模型解读")
        self.ai_button.clicked.connect(self.run_ai)
        layout.addWidget(self.ai_button)

        layout.addStretch(1)
        return panel

    def _build_result_area(self):
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.head = QLabel("尚未排盘")
        self.head.setObjectName("hint")
        self.head.setWordWrap(True)
        layout.addWidget(self.head)

        self.pillar_grid = QGridLayout()
        self.pillar_grid.setSpacing(8)
        pillars = QWidget()
        pillars.setLayout(self.pillar_grid)
        layout.addWidget(pillars)

        self.meta_box = QVBoxLayout()
        self.meta_box.setSpacing(6)
        layout.addLayout(self.meta_box)
        layout.addStretch(1)
        return area

    def _build_reading_area(self):
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        caption = QLabel("解读")
        caption.setObjectName("section")
        layout.addWidget(caption)
        self.browser = QTextBrowser()
        self.browser.setHtml(f"<div style='color:{TEXT_DIM};padding:16px;'>"
                             "先排四柱，再让模型从五行生克与当令之气给出取舍。</div>")
        layout.addWidget(self.browser, 1)
        return area

    # ---------- 排盘 ----------
    def calculate(self):
        moment = self.datetime_edit.dateTime()
        payload = {
            "year": moment.date().year(),
            "month": moment.date().month(),
            "day": moment.date().day(),
            "hour": moment.time().hour(),
            "minute": moment.time().minute(),
            "gender": self.gender_combo.currentText(),
        }
        self.calc_button.setEnabled(False)
        self.status.showMessage("正在排四柱…")
        self.worker = TaskWorker(daoyin.compute_bazi, parent=self, **payload)
        self.worker.finished.connect(self._on_result)
        self.worker.failed.connect(self._on_error)
        self.worker.start()

    def _on_error(self, message):
        self.calc_button.setEnabled(True)
        self.status.showMessage("排盘失败")
        QMessageBox.warning(self, "排盘失败", message)

    def _on_result(self, bazi):
        self.calc_button.setEnabled(True)
        self.bazi = bazi
        self._render()
        self.status.showMessage("四柱排盘完成")

    def _render(self):
        if not self.bazi:
            return
        data = self.bazi
        self.head.setText("　|　".join([
            data.get("solar", ""),
            data.get("lunar", ""),
            data.get("ganzhi", ""),
            f"日主 {data.get('day_master', '')}（{data.get('day_master_element', '')}）",
            data.get("qiyun", ""),
        ]))

        self._clear(self.pillar_grid)
        for index, pillar in enumerate(data.get("pillars", [])):
            name, ganzhi, shishen, wuxing, nayin, xunkong = pillar
            self.pillar_grid.addWidget(self._pillar_card(name, ganzhi, shishen, wuxing, nayin, xunkong), 0, index)

        self._clear(self.meta_box)
        period = data.get("fortune_period", {})
        meta = QLabel(
            f"三元九运：{period.get('period', '')} · {period.get('star', '')} · "
            f"{period.get('trigram', '')}宫当令（{period.get('element', '')}）"
        )
        meta.setStyleSheet(f"color:{GOLD};font-size:13px;")
        meta.setWordWrap(True)
        self.meta_box.addWidget(meta)

        jianchu = data.get("jianchu", {})
        jc = QLabel(f"建除十二神：{jianchu.get('name', '')} —— {jianchu.get('note', '')}")
        jc.setWordWrap(True)
        jc.setStyleSheet(f"color:{TEXT};font-size:12px;")
        self.meta_box.addWidget(jc)

        mansion = data.get("mansion", {})
        ms = QLabel(
            f"二十八宿参考：{mansion.get('name', '')}宿（{mansion.get('element', '')}·{mansion.get('animal', '')}）"
            f"　月建：{jianchu.get('month_branch', '')}"
        )
        ms.setWordWrap(True)
        ms.setStyleSheet(f"color:{TEXT};font-size:12px;")
        self.meta_box.addWidget(ms)

        wuxing = data.get("wuxing", {})
        wx = QLabel("五行计数：" + "　".join(f"{k}{v}" for k, v in wuxing.items()) +
                    f"　日主：{data.get('day_master', '')}（{data.get('day_master_element', '')}）")
        wx.setWordWrap(True)
        wx.setStyleSheet(f"color:{JADE};font-size:12px;")
        self.meta_box.addWidget(wx)

    def _pillar_card(self, name, ganzhi, shishen, wuxing, nayin, xunkong):
        card = QWidget()
        card.setObjectName("card")
        card.setStyleSheet("QWidget#card { background:#191a1f; border:1px solid #34353d; border-radius:4px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        title = QLabel(name)
        title.setStyleSheet(f"color:{GOLD};font-size:13px;")
        layout.addWidget(title)

        main = QLabel(ganzhi)
        main.setStyleSheet(f"color:{TEXT};font-size:22px;letter-spacing:4px;")
        layout.addWidget(main)

        for label, value in (("十神", shishen), ("五行", wuxing), ("纳音", nayin), ("旬空", xunkong)):
            row = QHBoxLayout()
            key = QLabel(label)
            key.setStyleSheet(f"color:{TEXT_DIM};font-size:11px;")
            key.setFixedWidth(34)
            val = QLabel(str(value))
            val.setStyleSheet(f"color:{TEXT};font-size:12px;")
            row.addWidget(key)
            row.addWidget(val)
            row.addStretch(1)
            layout.addLayout(row)

        hint = QLabel(PILLAR_HINTS.get(name, ""))
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color:{TEXT_DIM};font-size:11px;margin-top:2px;")
        layout.addWidget(hint)
        return card

    def _clear(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            child = item.layout()
            if child:
                self._clear(child)

    # ---------- AI ----------
    def run_ai(self):
        if not self.bazi:
            QMessageBox.information(self, "先排盘", "请先排四柱。")
            return

        def on_success(content):
            render_structured(self.browser, deepseek.extract_json(content))

        self.ai.run(daoyin_messages(self.bazi, self.focus_combo.currentText()), on_success, "四柱解读")
