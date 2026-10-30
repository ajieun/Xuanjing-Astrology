"""玄镜 · 命理工作台 入口。"""
import os
import sys

# 让 `python main.py` 与打包后的入口都能找到 app / vendor
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.resources import APP_NAME  # noqa: E402
from app.ui.main_window import MainWindow, apply_theme  # noqa: E402


def _smoke():
    """打包后自检：验证资源路径、排盘与起卦在冻结环境下可用。"""
    from app.resources import app_root, is_frozen

    print("frozen:", is_frozen(), "root:", app_root())
    from app import yijing, ziwei

    chart = ziwei.build_chart("1991-8-15", 1, "男", False, False, 2026)
    print("ziwei:", chart["gezhi_analysis"]["gezhi_name"])
    print("html:", ziwei.render_html(chart, ziwei.empty_reading()))
    print("yijing:", yijing.normalize(yijing.stalks())["ben_gua"])
    from app import knowledge

    print("knowledge:", len(knowledge.articles()))
    print("SMOKE OK")


def main():
    if "--smoke" in sys.argv:
        _smoke()
        return

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    apply_theme(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
