# -*- mode: python ; coding: utf-8 -*-
# ビルド方法: .venv\Scripts\pyinstaller.exe emc_report_tool.spec
#
# onedir（フォルダ）形式を採用する。onefile形式は起動のたびに一時フォルダへ
# 展開する必要があり、PySide6のQt DLLとWindows標準DLLの衝突など、
# 展開タイミング起因のトラブルが起きやすいため避ける。
#
# 出力先 dist/EmcReportTool/ には、ビルド後に「テンプレート」フォルダを
# 手動でコピーする必要がある（build_exe.ps1 参照）。ログ・バックアップ・
# Wordテンプレートはexe本体と同じフォルダを基準に読み書きする
# （src/utils/app_paths.py）。

import sys
from pathlib import Path

# このvenvはAnaconda配布のPythonから作られており、sqlite3モジュールが読み込む
# 実体のsqlite3.dllはAnaconda本体の Library/bin にある（venv側にはコピーされない）。
# 開発時はconda由来のPATH設定で見つかるが、exe単体では見つからずクラッシュするため、
# 明示的にバンドルする。python.orgの通常配布のPythonでビルドする場合は不要
# （sqlite3が実行ファイルに静的リンクされているため、このDLLは存在しない）。
_binaries = []
_conda_sqlite_dll = Path(sys.base_prefix) / "Library" / "bin" / "sqlite3.dll"
if _conda_sqlite_dll.exists():
    _binaries.append((str(_conda_sqlite_dll), "."))

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=_binaries,
    datas=[
        ('src/database/migrations', 'database/migrations'),
    ],
    hiddenimports=[],
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
    name='EmcReportTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='EmcReportTool',
)
