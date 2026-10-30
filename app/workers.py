"""后台工作线程：命理计算与模型调用都放到线程里，避免界面卡死。"""
from PySide6.QtCore import QThread, Signal

from . import deepseek


class ChatWorker(QThread):
    """调用 DeepSeek 对话接口。"""

    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, messages, settings, parent=None):
        super().__init__(parent)
        self.messages = messages
        self.settings = settings

    def run(self):
        try:
            content, _ = deepseek.chat(self.messages, self.settings)
        except Exception as exc:  # noqa: BLE001 - 线程内统一转成界面提示
            self.failed.emit(str(exc))
            return
        self.finished.emit(content)


class TaskWorker(QThread):
    """执行任意可调用对象（排盘、八字、起卦等）。"""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, func, *args, parent=None, **kwargs):
        super().__init__(parent)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)
