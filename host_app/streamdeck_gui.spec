from pathlib import Path

project = Path(SPECPATH)
app_icon_svg = str(
    project / "streamdeck_monitor" / "gui" / "assets" / "app_icon.svg"
)
app_icon_ico = str(project / "build" / "app_icon.ico")

analysis = Analysis(
    [str(project / "streamdeck_monitor" / "gui" / "bootstrap.py")],
    pathex=[str(project)],
    binaries=[],
    datas=[
        (
            app_icon_svg,
            "streamdeck_monitor/gui/assets",
        )
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="StreamDeckMini",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=app_icon_ico,
)

collect = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="StreamDeckMini",
)
