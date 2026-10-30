"""紫微斗数排盘页面。"""
import json
import os
from datetime import date

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .. import deepseek, ziwei
from ..prompts import ziwei_messages
from ..resources import user_dir
from ..workers import TaskWorker
from .ai import AiRunner, render_ziwei_reading
from .palace_card import PalaceCard
from .theme import CINNABAR, GOLD, JADE, TEXT_DIM

HOUR_ITEMS = [
    ("早子时 23-01", 0), ("丑时 01-03", 1), ("寅时 03-05", 2), ("卯时 05-07", 3),
    ("辰时 07-09", 4), ("巳时 09-11", 5), ("午时 11-13", 6), ("未时 13-15", 7),
    ("申时 15-17", 8), ("酉时 17-19", 9), ("戌时 19-21", 10), ("亥时 21-23", 11),
    ("晚子时 23-01", 12),
]

FOCUS_ITEMS = [
    "全面解读", "只看事业", "只看财运", "只看感情婚姻", "只看当前大限", "只看流年运势", "性格与天赋",
]


class ZiweiView(QWidget):
    def __init__(self, settings_getter, status, parent=None):
        super().__init__(parent)
        self.settings_getter = settings_getter
        self.status = status
        self.chart = None
        self.reading = ziwei.empty_reading()
        self.worker = None

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        root.addWidget(self._build_form(), 0)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self._build_chart_area())
        self.splitter.addWidget(self._build_reading_area())
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        root.addWidget(self.splitter, 1)

        self.ai = AiRunner(self, self.browser, status, settings_getter, self.ai_button)

    # ---------- 界面 ----------
    def _build_form(self):
        panel = QWidget()
        panel.setFixedWidth(268)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("生辰信息")
        title.setObjectName("section")
        layout.addWidget(title)

        self.calendar_combo = QComboBox()
        self.calendar_combo.addItems(["公历", "农历"])
        layout.addWidget(self._row("历法", self.calendar_combo))

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(date(1990, 1, 1))
        layout.addWidget(self._row("日期", self.date_edit))

        self.hour_combo = QComboBox()
        for label, value in HOUR_ITEMS:
            self.hour_combo.addItem(label, value)
        self.hour_combo.setCurrentIndex(5)
        layout.addWidget(self._row("时辰", self.hour_combo))

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女"])
        layout.addWidget(self._row("性别", self.gender_combo))

        self.leap_check = QCheckBox("农历闰月")
        layout.addWidget(self.leap_check)

        self.year_spin = QComboBox()
        current = date.today().year
        for year in range(current - 30, current + 31):
            self.year_spin.addItem(str(year), year)
        self.year_spin.setCurrentText(str(current))
        layout.addWidget(self._row("流年", self.year_spin))

        self.cast_button = QPushButton("排盘")
        self.cast_button.setObjectName("primary")
        self.cast_button.clicked.connect(self.cast)
        layout.addWidget(self.cast_button)

        hint = QLabel("排盘全部由本地规则引擎计算，不依赖模型，结果可复现。")
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

        self.ai_button = QPushButton("请模型解读命盘")
        self.ai_button.clicked.connect(self.run_ai)
        layout.addWidget(self.ai_button)

        self.export_button = QPushButton("导出命盘 HTML")
        self.export_button.clicked.connect(self.export_html)
        layout.addWidget(self.export_button)

        self.save_button = QPushButton("保存解读 JSON")
        self.save_button.clicked.connect(self.save_reading)
        layout.addWidget(self.save_button)

        layout.addStretch(1)
        return panel

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

    def _build_chart_area(self):
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.summary = QLabel("尚未排盘")
        self.summary.setObjectName("hint")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        self.grid = QGridLayout()
        self.grid.setSpacing(6)
        grid_widget = QWidget()
        grid_widget.setLayout(self.grid)
        layout.addWidget(grid_widget, 1)

        self.gezhi_box = QVBoxLayout()
        self.gezhi_box.setSpacing(6)
        layout.addLayout(self.gezhi_box)

        self.travel_table = QTableWidget(0, 4)
        self.travel_table.setHorizontalHeaderLabels(["宫位", "压力分", "风险评级", "触发源"])
        self.travel_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.travel_table.verticalHeader().setVisible(False)
        self.travel_table.setMaximumHeight(190)
        layout.addWidget(self.travel_table)
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
        self.browser.setOpenExternalLinks(True)
        self.browser.setHtml(f"<div style='color:{TEXT_DIM};padding:16px;'>"
                             "先排盘，再让模型把星曜语言翻译成人话。</div>")
        layout.addWidget(self.browser, 1)
        return area

    # ---------- 排盘 ----------
    def cast(self):
        selected = self.date_edit.date()
        date_str = f"{selected.year()}-{selected.month()}-{selected.day()}"
        is_lunar = self.calendar_combo.currentIndex() == 1
        payload = {
            "date_str": date_str,
            "hour_index": self.hour_combo.currentData(),
            "gender": self.gender_combo.currentText(),
            "is_lunar": is_lunar,
            "is_leap": self.leap_check.isChecked(),
            "target_year": int(self.year_spin.currentText()),
        }
        self.status.showMessage("正在排盘…")
        self.cast_button.setEnabled(False)
        self.worker = TaskWorker(ziwei.build_chart, parent=self, **payload)
        self.worker.finished.connect(self._on_chart)
        self.worker.failed.connect(self._on_error)
        self.worker.start()

    def _on_error(self, message):
        self.cast_button.setEnabled(True)
        self.status.showMessage("排盘失败")
        QMessageBox.warning(self, "排盘失败", message)

    def _on_chart(self, chart):
        self.cast_button.setEnabled(True)
        self.chart = chart
        self.reading = ziwei.empty_reading()
        self._render_chart()
        self.status.showMessage("排盘完成")

    def _render_chart(self):
        chart = self.chart
        if not chart:
            return

        soul = ziwei.soul_palace(chart)
        soul_branch = chart.get("soul_palace_branch", "")
        limit_branch = self._limit_branch(chart)

        summary_bits = [
            f"农历 {chart.get('lunar_date') or '—'}",
            f"公历 {chart.get('solar_date') or '—'}",
            f"{chart.get('gender', '')}命",
            chart.get("five_elements", ""),
            f"命宫 {soul_branch}宫",
            f"身宫 {chart.get('body_palace_branch', '')}宫",
        ]
        stars = "·".join(soul.get("major_stars", [])) if soul and soul.get("major_stars") else "空宫（借对宫）"
        summary_bits.append(f"命宫主星 {stars}")
        self.summary.setText("　|　".join(summary_bits))

        self._render_grid(soul_branch, limit_branch)
        self._render_gezhi()
        self._render_travel()

    def _limit_branch(self, chart):
        travel = chart.get("time_travel_analysis") or {}
        palace_name = travel.get("current_decadal_palace")
        if not palace_name:
            return ""
        palace = next((p for p in chart["palaces"] if p["name"] == palace_name), None)
        return palace["earthly_branch"] if palace else ""

    def _render_grid(self, soul_branch, limit_branch):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        by_branch = ziwei.palace_by_branch(self.chart)
        for branch, row, col in ziwei.BRANCH_GRID:
            palace = by_branch.get(branch)
            if not palace:
                continue
            card = PalaceCard(palace, soul_branch, limit_branch, self)
            card.clicked.connect(self._show_palace)
            self.grid.addWidget(card, row, col)

        center = QLabel(self._center_text())
        center.setAlignment(Qt.AlignCenter)
        center.setWordWrap(True)
        center.setStyleSheet(f"color:{TEXT_DIM};font-size:12px;line-height:1.7;padding:12px;")
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.addWidget(center)
        self.grid.addWidget(center_widget, 1, 1, 2, 2)

    def _center_text(self):
        chart = self.chart
        mutagens = chart.get("year_mutagens", [])
        tags = "　".join(f"{m['star']}{m['mutagen']}" for m in mutagens) or "—"
        return (
            f"{chart.get('chinese_date', '')}<br>"
            f"五行局：{chart.get('five_elements', '')}<br>"
            f"生年四化：{tags}"
        )

    def _render_gezhi(self):
        layout = self.gezhi_box
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        gezhi = self.chart.get("gezhi_analysis") or {}
        if not gezhi:
            return

        name = QLabel(f"格局：{gezhi.get('gezhi_name', '—')}")
        name.setStyleSheet(f"color:{GOLD};font-size:14px;")
        layout.addWidget(name)

        desc = QLabel(gezhi.get("description", ""))
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{TEXT_DIM};font-size:12px;line-height:1.7;")
        layout.addWidget(desc)

        metrics = gezhi.get("quant_metrics", {})
        for label, key in (("风险耐受度", "risk_tolerance"), ("波动恢复力", "fluctuation_resilience"),
                           ("决策激进度", "decision_aggressiveness")):
            value = int(metrics.get(key, 3))
            row = QHBoxLayout()
            caption = QLabel(f"{label} {value}/5")
            caption.setObjectName("metric")
            caption.setFixedWidth(110)
            bar = QProgressBar()
            bar.setRange(0, 5)
            bar.setValue(value)
            bar.setFixedHeight(8)
            bar.setTextVisible(False)
            row.addWidget(caption)
            row.addWidget(bar, 1)
            container = QWidget()
            container.setLayout(row)
            layout.addWidget(container)

        for warning in gezhi.get("stress_warnings", []):
            tip = QLabel(f"⚠ {warning.get('type', '')}：{warning.get('desc', '')}")
            tip.setWordWrap(True)
            tip.setStyleSheet(f"color:{CINNABAR if warning.get('code') else JADE};font-size:12px;")
            layout.addWidget(tip)

    def _render_travel(self):
        travel = self.chart.get("time_travel_analysis") or {}
        rows = travel.get("full_time_log", [])
        self.travel_table.setRowCount(len(rows))
        for index, item in enumerate(rows):
            values = [
                f"{item.get('palace_name', '')} {item.get('earthly_branch', '')}",
                str(item.get("stress_score", "")),
                item.get("risk_level", ""),
                "；".join(item.get("trigger_sources", [])),
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col == 1 and item.get("is_hotspot"):
                    cell.setForeground(QColor(CINNABAR))
                self.travel_table.setItem(index, col, cell)
        self.travel_table.resizeColumnsToContents()

    def _show_palace(self, palace):
        major = "、".join(palace.get("major_stars", [])) or "空宫"
        minor = "、".join(palace.get("minor_stars", [])) or "—"
        borrowed = "、".join(palace.get("borrowed_major_stars", [])) or "—"
        mutagens = "、".join(f"{m['star']}{m['mutagen']}" for m in palace.get("mutagens", [])) or "—"
        QMessageBox.information(
            self,
            f"{palace.get('name', '')} · {palace.get('earthly_branch', '')}宫",
            "\n".join([
                f"宫位干支：{palace.get('dizhi', '')}",
                f"主星：{major}",
                f"辅星：{minor}",
                f"借星：{borrowed}",
                f"四化：{mutagens}",
                f"大限：{palace.get('decadal_range', '')} 岁（{palace.get('decadal_dizhi', '')}）",
                f"能量系数：{palace.get('energy_coefficient', 1.0)}",
            ]),
        )

    # ---------- AI ----------
    def run_ai(self):
        if not self.chart:
            QMessageBox.information(self, "先排盘", "请先点「排盘」生成命盘，再做解读。")
            return

        def on_success(content):
            self.reading = deepseek.extract_json(content)
            current = self.reading.get("current_decadal_display", "")
            render_ziwei_reading(self.browser, self.reading, header=f"当前大限：{current}" if current else "")
            self.status.showMessage("解读完成，可用「导出命盘 HTML」生成完整报告")

        self.ai.run(ziwei_messages(self.chart, self.focus_combo.currentText()), on_success, "命盘解读")

    def export_html(self):
        if not self.chart:
            QMessageBox.information(self, "先排盘", "请先排盘。")
            return
        default_dir = user_dir()
        path, _ = QFileDialog.getSaveFileName(
            self, "导出命盘", os.path.join(default_dir, "命盘.html"), "HTML 文件 (*.html)")
        if not path:
            return
        try:
            temp = ziwei.render_html(self.chart, self.reading)
            with open(temp, "r", encoding="utf-8") as source:
                html = source.read()
            with open(path, "w", encoding="utf-8") as target:
                target.write(html)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "导出失败", str(exc))
            return
        self.status.showMessage(f"已导出：{path}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def save_reading(self):
        if not self.reading.get("cards"):
            QMessageBox.information(self, "暂无解读", "请先让模型生成解读。")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存解读", os.path.join(user_dir(), "reading.json"), "JSON 文件 (*.json)")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.reading, handle, ensure_ascii=False, indent=2)
        self.status.showMessage(f"已保存：{path}")
