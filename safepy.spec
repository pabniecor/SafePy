# safepy.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

project_root = Path(__name__).parent

hiddenimports = []
hiddenimports += collect_submodules("app")

datas = [
    (str(project_root / "app" / "ui" / "styles" / "main.qss"), "app/ui/styles"),
    (str(project_root / "app" / "ui" / "styles" / "icon.ico"), "app/ui/styles"),
    (str(project_root / "app" / "persistence" / "schema.sql"), "app/persistence"),
    (str(project_root / "data" / "sample_requirements.txt"), "data"),
]

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SafePy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(project_root / "app" / "ui" / "styles" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SafePy",
)