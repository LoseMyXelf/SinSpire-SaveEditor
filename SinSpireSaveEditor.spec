# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["save_editor_gui.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("save_editor_app_icon.ico", "."),
        ("save_editor_app_icon.png", "."),
        ("sinspire_icon.png", "."),
        ("sinspire_icon.ico", "."),
    ],
    hiddenimports=[],
    hookspath=["."],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Sin Spire Save Editor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["sinspire_icon.ico"],
)
