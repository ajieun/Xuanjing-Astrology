"""主窗口。"""
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import config
from ..resources import APP_NAME, user_dir
from .daoyin_view import DaoyinView
from .knowledge_view import KnowledgeView
from .settings_dialog import SettingsDialog
from .tarot_view import TarotView
from .theme import TEXT_DIM, stylesheet
from .yijing_view import YijingView
from .ziwei_view import ZiweiView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = config.load()
        self.setWindowTitle(f"{APP_NAME} · 紫微 · 周易 · 道家 · 塔罗")
        self.resize(1360, 880)
        self.setMinimumSize(1180, 720)

        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addLayout(self._build_header())
        root.addWidget(self._build_tabs(), 1)
        root.addLayout(self._build_footer())
        self.setCentralWidget(container)

        self.statusBar().showMessage("就绪")

    def _build_header(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(22, 18, 22, 12)
        layout.setSpacing(12)

        title = QLabel("玄　镜")
        title.setObjectName("title")
        layout.addWidget(title)

        subtitle = QLabel("紫微斗数 · 周易筮法 · 道家术数 · 塔罗")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        layout.addStretch(1)

        self.settings_button = QPushButton("设置")
        self.settings_button.setObjectName("ghost")
        self.settings_button.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_button)

        about = QPushButton("关于")
        about.setObjectName("ghost")
        about.clicked.connect(self.show_about)
        layout.addWidget(about)
        return layout

    def _build_tabs(self):
        status = self.statusBar()
        self.tabs = QTabWidget()
        self.ziwei_view = ZiweiView(lambda: self.settings, status)
        self.yijing_view = YijingView(lambda: self.settings, status)
        self.daoyin_view = DaoyinView(lambda: self.settings, status)
        self.tarot_view = TarotView(lambda: self.settings, status)
        self.knowledge_view = KnowledgeView(status)

        self.tabs.addTab(self.ziwei_view, "紫微斗数")
        self.tabs.addTab(self.yijing_view, "周易筮法")
        self.tabs.addTab(self.daoyin_view, "道家术数")
        self.tabs.addTab(self.tarot_view, "塔罗")
        self.tabs.addTab(self.knowledge_view, "典籍")
        return self.tabs

    def _build_footer(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(22, 6, 22, 10)
        note = QLabel(
            "象由心生，命由象推 —— 命盘显示可能性，行动决定现实；"
            "本工具仅供参考与自省，不作医疗、法律与投资决策依据。"
        )
        note.setStyleSheet(f"color:{TEXT_DIM};font-size:11px;")
        layout.addWidget(note)
        layout.addStretch(1)
        path = QLabel(f"本机数据目录：{user_dir()}")
        path.setStyleSheet(f"color:{TEXT_DIM};font-size:11px;")
        layout.addWidget(path)
        return layout

    def open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.settings = config.save(dialog.result_settings())
            self.statusBar().showMessage("设置已保存")

    def show_about(self):
        QMessageBox.information(
            self,
            "关于",
            "\n".join([
                f"{APP_NAME}",
                "",
                "紫微排盘：mingli-master（MIT）+ iztro-py",
                "周易筮法：ichingshifa（MIT）大衍筮法 / 纳甲",
                "道家术数：lunar-python 农历库 + 三元九运、建除十二神",
                "塔罗：内置 78 张韦特牌组与 6 种牌阵（含凯尔特十字）",
                "AI 解读：DeepSeek（OpenAI 兼容接口）",
                "",
                f"配置与导出目录：{user_dir()}",
            ]),
        )

    def closeEvent(self, event):  # noqa: N802
        for view in (self.ziwei_view, self.yijing_view, self.daoyin_view, self.tarot_view):
            for worker in (getattr(view, "worker", None), getattr(view.ai, "worker", None)):
                if worker is not None and worker.isRunning():
                    worker.quit()
                    worker.wait(2000)
        super().closeEvent(event)


def apply_theme(app):
    app.setStyleSheet(stylesheet())
