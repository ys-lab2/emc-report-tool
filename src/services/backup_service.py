from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from services.project_service import ProjectHandle
from utils.app_paths import app_base_dir

BACKUP_DIR = app_base_dir() / "backup"


def create_backup(handle: ProjectHandle, generations: int) -> Path:
    """現在のプロジェクトファイルを backup/ へ世代コピーし、
    generations を超えた古い世代を削除する（61.節）。"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    handle.connection.execute("PRAGMA wal_checkpoint(FULL);")

    stem = handle.file_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_path = BACKUP_DIR / f"{stem}_{timestamp}.emcproj"
    shutil.copyfile(handle.file_path, backup_path)

    _prune_old_backups(stem, generations)
    return backup_path


def _prune_old_backups(stem: str, generations: int) -> None:
    existing = sorted(
        BACKUP_DIR.glob(f"{stem}_*.emcproj"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old_backup in existing[generations:]:
        old_backup.unlink(missing_ok=True)
