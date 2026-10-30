"""资源路径与本地知识库定位。

打包成 exe 后源码不在文件系统中，必须区分两种运行形态：
    - 冻结模式：资源位于 PyInstaller 的临时解压目录 `sys._MEIPASS`
    - 开发模式：资源位于仓库根目录
"""
import os
import sys

APP_NAME = "玄镜命理工作台"


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def app_root():
    """资源根目录（只读）：模板、典籍、vendored 源码。"""
    if is_frozen():
        return os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)), "resources")
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def user_dir():
    """用户数据目录（可写）：配置、导出文件。"""
    base = os.environ.get("MINGPAN_HOME")
    if not base:
        if is_frozen():
            base = os.path.join(os.path.expanduser("~"), "Documents", APP_NAME)
        else:
            base = os.path.join(app_root(), ".data")
    os.makedirs(base, exist_ok=True)
    return base


def resource(*parts):
    return os.path.join(app_root(), *parts)


def vendor(*parts):
    return os.path.join(app_root(), "vendor", *parts)


def vendor_mingli(*parts):
    return os.path.join(app_root(), "vendor", "mingli_master", *parts)


def knowledge_dir():
    return vendor_mingli("references")


def load_text(*parts):
    path = resource(*parts)
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def load_vendor_module(module_dir, module_name):
    """按路径加载 vendored 脚本（如 mingli-master 的排盘/渲染脚本）。"""
    import importlib.util

    path = os.path.join(module_dir, f"{module_name}.py")
    spec = importlib.util.spec_from_file_location(f"_mingpan_vendor_{module_name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
