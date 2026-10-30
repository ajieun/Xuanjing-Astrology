"""界面侧的 AI 调用封装：统一状态提示、错误处理与结果渲染。"""
import html

from PySide6.QtWidgets import QMessageBox

from .. import deepseek, prompts
from ..workers import ChatWorker
from .theme import GOLD, LINE, PANEL, TEXT_DIM, markdown_to_html, reading_card_html


class AiRunner:
    """在界面里安全地把请求发给 DeepSeek，并把结果渲染到 QTextBrowser。"""

    def __init__(self, owner, output_widget, status=None, settings_getter=None, button=None):
        self.owner = owner
        self.output = output_widget
        self.status = status
        self.settings_getter = settings_getter
        self.button = button
        self.worker = None

    def _say(self, text):
        if self.status:
            self.status.showMessage(text)

    def busy(self, running, label=""):
        if self.button:
            self.button.setEnabled(not running)
            self.button.setText("解读中…" if running else label or self.button.text())

    def run(self, messages, on_success, title="AI 解读"):
        settings = self.settings_getter() if self.settings_getter else {}
        if not str(settings.get("api_key", "")).strip():
            QMessageBox.information(self.owner, "需要配置", "请先在右上角「设置」里填写 DeepSeek API Key。")
            return False
        if self.worker is not None and self.worker.isRunning():
            self._say("上一次请求还在进行中…")
            return False

        self._say(f"{title}请求已发出，等待模型返回…")
        self.output.setHtml(
            f"<div style='color:{TEXT_DIM};padding:20px;'>正在请求模型解读，通常 20-60 秒…</div>"
        )
        self.worker = ChatWorker(messages, settings, self.owner)

        def on_done(content):
            self.busy(False)
            try:
                on_success(content)
                self._say(f"{title}完成")
            except Exception as exc:  # noqa: BLE001
                self.output.setPlainText(content)
                self._say(f"解析模型结果失败：{exc}")

        def on_failed(message):
            self.busy(False)
            self.output.setHtml(f"<div style='color:#d0654f;padding:16px;'>{html.escape(message)}</div>")
            self._say(f"{title}失败")
            QMessageBox.warning(self.owner, f"{title}失败", message)

        self.worker.finished.connect(on_done)
        self.worker.failed.connect(on_failed)
        self.worker.start()
        return True


def render_ziwei_reading(browser, reading, header=""):
    """渲染紫微解读（HTML 卡片 + 校准问题）。"""
    cards = reading.get("cards", []) or []
    parts = []
    if header:
        parts.append(f"<div style='color:{TEXT_DIM};font-size:12px;margin-bottom:6px;'>{html.escape(header)}</div>")
    for card in cards:
        parts.append(reading_card_html(card))

    questions = reading.get("calibration_questions", []) or []
    if questions:
        items = "".join(
            f"<li style='margin:6px 0;'>{html.escape(str(q.get('text', '')))}"
            f"<span style='color:{TEXT_DIM};'> {html.escape(str(q.get('hint', '')))}</span></li>"
            for q in questions
        )
        parts.append(
            "<div style='border:1px dashed #34353d;border-radius:4px;padding:14px 16px;margin:16px 0;'>"
            "<div style='color:#c8a35a;font-size:14px;'>校准问答</div>"
            f"<ul style='margin:8px 0 0 18px;line-height:1.8;'>{items}</ul></div>"
        )

    if not parts:
        parts.append(f"<div style='color:{TEXT_DIM};padding:16px;'>暂无解读内容。</div>")
    browser.setHtml(
        "<div style='font-family:'PingFang SC','Microsoft YaHei',sans-serif;'>" + "".join(parts) + "</div>"
    )


def render_markdown(browser, markdown_text):
    browser.setHtml(markdown_to_html(markdown_text))


def render_structured(browser, data, title_key="overall", cards_key=None):
    """渲染周易/道家/塔罗这类结构化结果。"""
    overall = data.get(title_key, "")
    parts = [f"<div style='font-size:15px;line-height:1.9;margin-bottom:10px;'>{markdown_to_html(overall)}</div>"]

    for card in data.get(cards_key or "__none__", []) or []:
        if not isinstance(card, dict):
            continue
        position = card.get("position", "")
        name = card.get("card", "")
        reading = markdown_to_html(str(card.get("reading", "")))
        parts.append(
            f"<div style='border:1px solid {LINE};border-left:3px solid {GOLD};border-radius:4px;"
            f"padding:12px 14px;margin:10px 0;background:{PANEL};'>"
            f"<div style='color:{GOLD};font-size:13px;'>{html.escape(position)}"
            f"<span style='color:{TEXT_DIM};'> · {html.escape(name)}</span></div>"
            f"<div style='margin-top:8px;line-height:1.85;'>{reading}</div></div>"
        )

    for key, label in (("lines_reading", "爻辞白话"), ("actions", "宜"), ("cautions", "忌"), ("advice", "建议")):
        values = data.get(key) or []
        if not values:
            continue
        items = "".join(f"<li style='margin:5px 0;line-height:1.7;'>{markdown_to_html(str(v))}</li>" for v in values)
        parts.append(
            f"<div style='margin:12px 0;'><div style='color:#c8a35a;'>{label}</div>"
            f"<ul style='margin:6px 0 0 18px;'>{items}</ul></div>"
        )

    for section in data.get("sections", []) or []:
        parts.append(reading_card_html(section))

    timing = data.get("timing")
    if timing:
        parts.append(
            f"<div style='border-left:3px solid #6fa08a;padding:10px 14px;margin:14px 0;'>"
            f"<span style='color:#6fa08a;'>时机</span> {markdown_to_html(str(timing))}</div>"
        )

    browser.setHtml("".join(parts))


def test_connection(owner, settings):
    try:
        reply = deepseek.test_connection(settings)
    except Exception as exc:  # noqa: BLE001
        QMessageBox.warning(owner, "连接失败", str(exc))
        return False
    QMessageBox.information(owner, "连接成功", f"已连通：{reply}")
    return True


__all__ = [
    "AiRunner",
    "render_ziwei_reading",
    "render_markdown",
    "render_structured",
    "test_connection",
    "prompts",
]
