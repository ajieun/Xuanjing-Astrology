"""典籍与知识库页面。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .. import knowledge
from .theme import GOLD, TEXT_DIM, markdown_to_html


class KnowledgeView(QWidget):
    def __init__(self, status, parent=None):
        super().__init__(parent)
        self.status = status
        self.items = knowledge.articles()

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("典籍")
        title.setObjectName("section")
        header.addWidget(title)
        header.addStretch(1)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("检索关键字（如：化忌、贪狼、上善若水）")
        self.search_edit.setFixedWidth(320)
        self.search_edit.textChanged.connect(self._filter)
        header.addWidget(self.search_edit)
        root.addLayout(header)

        self.splitter = QSplitter(Qt.Horizontal)
        self.list = QListWidget()
        self.list.setFixedWidth(268)
        self.list.currentRowChanged.connect(self._show_current)
        self.splitter.addWidget(self.list)

        self.browser = QTextBrowser()
        self.browser.setHtml(f"<div style='color:{TEXT_DIM};padding:20px;'>"
                             "左侧选择一篇典籍。内容全部来自本地文件，离线可用。</div>")
        self.splitter.addWidget(self.browser)
        self.splitter.setStretchFactor(1, 1)
        root.addWidget(self.splitter, 1)

        self._fill(self.items)
        if self.items:
            self.list.setCurrentRow(0)

    def _fill(self, items):
        self.list.blockSignals(True)
        self.list.clear()
        for title, _ in items:
            self.list.addItem(title)
        self.list.blockSignals(False)

    def _filter(self, text):
        self.items = knowledge.search(text)
        self._fill(self.items)
        if self.items:
            self.list.setCurrentRow(0)
        else:
            self.browser.setHtml(f"<div style='color:{TEXT_DIM};padding:20px;'>没有匹配的典籍。</div>")

    def _show_current(self, row):
        if row < 0 or row >= len(self.items):
            return
        title, body = self.items[row]
        self.status.showMessage(f"典籍：{title}")
        highlighted = f"<div style='color:{GOLD};font-size:17px;margin-bottom:14px;'>{title}</div>"
        self.browser.setHtml(highlighted + markdown_to_html(body))
