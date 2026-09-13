from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """PyInstaller等でexe化された状態で実行されているかを判定する。"""
    return getattr(sys, "frozen", False)


def app_base_dir() -> Path:
    """ログ・バックアップ・Wordテンプレートなど、実行時に書き込み・差し替えが必要な
    ファイルの基準ディレクトリ。exe化時はexe自身が置かれているフォルダ、
    開発時はプロジェクトルート（このファイルの3階層上）を返す。

    PyInstallerのonefileモードは実行のたびに一時フォルダへ展開するため、
    そこに書き込んでも次回起動時には消えてしまう。ログやバックアップ、
    ユーザーが差し替える可能性のあるWordテンプレートは、必ずこちらを使うこと。"""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent
