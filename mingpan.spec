# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：生成单文件 Windows exe。"""

import os

# ichingshifa 的六十四卦数据库（data.pkl）必须随包分发，否则冻结运行时找不到
try:
    import ichingshifa as _ichingshifa

    ichingshifa_dir = os.path.dirname(os.path.abspath(_ichingshifa.__file__))
except Exception:  # noqa: BLE001
    ichingshifa_dir = ""

ichingshifa_data = os.path.join(ichingshifa_dir, "data.pkl") if ichingshifa_dir else ""

datas = [
    ("templates/chart_template.html", "resources/templates"),
    ("SKILL.md", "resources"),
    ("vendor/sxtwl_compat.py", "resources/vendor"),
    ("vendor/__init__.py", "resources/vendor"),
    (ichingshifa_data, "ichingshifa"),
    ("vendor/mingli_master/scripts", "resources/vendor/mingli_master/scripts"),
    ("vendor/mingli_master/templates", "resources/vendor/mingli_master/templates"),
    ("vendor/mingli_master/references", "resources/vendor/mingli_master/references"),
]

hiddenimports = [
    "lunar_python",
    "ephem",
    "numpy",
    "cn2an",
    "iztro_py",
    "pydantic",
    "pydantic.deprecated.decorator",
    "ichingshifa",
    "ichingshifa.ichingshifa",
]

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.Qt3DCore",
        "PySide6.QtMultimedia",
        "PySide6.QtBluetooth",
        "PySide6.QtNfc",
        "PySide6.QtPositioning",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtSql",
        "PySide6.QtTest",
        "PySide6.QtDesigner",
        "PySide6.QtHelp",
        "PySide6.QtOpenGL",
        "PySide6.QtOpenGLWidgets",
        "PySide6.QtNetworkAuth",
        "PySide6.QtRemoteObjects",
        "PySide6.QtScxml",
        "PySide6.QtSpatialAudio",
        "PySide6.QtStateMachine",
        "PySide6.QtTextToSpeech",
        "PySide6.QtUiTools",
        "PySide6.QtWebChannel",
        "PySide6.QtWebSockets",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtHttpServer",
        "PySide6.QtQuickWidgets",
        "matplotlib",
        "scipy",
        "pandas",
        "tkinter",
        "notebook",
        "PIL",
        "pytest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="玄镜命理工作台",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
