"""DeepSeek 接口设置。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from .. import config
from .ai import test_connection
from .theme import GOLD

MODELS = ["deepseek-chat", "deepseek-reasoner"]


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("模型接口设置")
        self.setMinimumWidth(520)
        self.settings = dict(settings)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QLabel("DeepSeek 接口")
        title.setObjectName("section")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.key_edit = QLineEdit(self.settings.get("api_key", ""))
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText("sk-xxxxxxxxxxxxxxxx")

        self.toggle = QPushButton("显示")
        self.toggle.setFixedWidth(58)
        self.toggle.clicked.connect(self._toggle_key)
        key_row = QHBoxLayout()
        key_row.setSpacing(6)
        key_row.addWidget(self.key_edit, 1)
        key_row.addWidget(self.toggle)
        form.addRow("API Key", key_row)

        self.url_edit = QLineEdit(self.settings.get("base_url", config.DEFAULT_BASE_URL))
        form.addRow("接口地址", self.url_edit)

        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems(MODELS)
        current_model = self.settings.get("model", config.DEFAULT_MODEL)
        self.model_combo.setCurrentText(current_model)
        form.addRow("模型", self.model_combo)

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.05)
        self.temp_spin.setValue(float(self.settings.get("temperature", 0.85)))
        form.addRow("温度", self.temp_spin)

        self.token_spin = QSpinBox()
        self.token_spin.setRange(512, 32768)
        self.token_spin.setSingleStep(256)
        self.token_spin.setValue(int(self.settings.get("max_tokens", 4096)))
        form.addRow("最大 Token", self.token_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(30, 900)
        self.timeout_spin.setSingleStep(30)
        self.timeout_spin.setValue(int(self.settings.get("timeout", config.DEFAULT_TIMEOUT)))
        form.addRow("超时（秒）", self.timeout_spin)

        layout.addLayout(form)

        hint = QLabel("Key 保存在本机用户目录，不会随报告导出。")
        hint.setObjectName("hint")
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.test_button = QPushButton("测试连接")
        self.test_button.clicked.connect(self._test)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        self.save_button = QPushButton("保存")
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self._save)
        buttons.addWidget(self.test_button)
        buttons.addWidget(cancel)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)

    def _toggle_key(self):
        if self.key_edit.echoMode() == QLineEdit.Password:
            self.key_edit.setEchoMode(QLineEdit.Normal)
            self.toggle.setText("隐藏")
        else:
            self.key_edit.setEchoMode(QLineEdit.Password)
            self.toggle.setText("显示")

    def _collect(self):
        return {
            "api_key": self.key_edit.text().strip(),
            "base_url": self.url_edit.text().strip() or config.DEFAULT_BASE_URL,
            "model": self.model_combo.currentText().strip() or config.DEFAULT_MODEL,
            "temperature": self.temp_spin.value(),
            "max_tokens": self.token_spin.value(),
            "timeout": self.timeout_spin.value(),
        }

    def _test(self):
        test_connection(self, self._collect())

    def _save(self):
        self.settings = self._collect()
        self.accept()

    def result_settings(self):
        return self.settings
