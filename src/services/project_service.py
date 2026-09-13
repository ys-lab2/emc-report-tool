from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from database.connection import create_connection
from database.migration_runner import apply_migrations
from models.project import Project
from repositories import project_repository
from utils.time_utils import now_iso
from utils.uuid_utils import new_id


@dataclass
class ProjectHandle:
    connection: sqlite3.Connection
    project: Project
    file_path: Path

    def close(self) -> None:
        self.connection.close()


def create_new(file_path: str | Path) -> ProjectHandle:
    path = Path(file_path)
    if path.exists():
        raise FileExistsError(f"すでにファイルが存在します: {path}")

    conn = create_connection(path)
    apply_migrations(conn)

    timestamp = now_iso()
    project = Project(
        project_id=new_id(),
        created_at=timestamp,
        updated_at=timestamp,
    )
    project_repository.insert(conn, project)

    return ProjectHandle(connection=conn, project=project, file_path=path)


def open_project(file_path: str | Path) -> ProjectHandle:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"プロジェクトファイルが見つかりません: {path}")

    conn = create_connection(path)
    apply_migrations(conn)

    project = project_repository.get_first(conn)
    if project is None:
        raise ValueError(f"プロジェクトデータが見つかりません: {path}")

    return ProjectHandle(connection=conn, project=project, file_path=path)


def save(handle: ProjectHandle) -> None:
    handle.project.updated_at = now_iso()
    project_repository.update(handle.connection, handle.project)
    handle.connection.execute("PRAGMA wal_checkpoint(FULL);")


def save_as(handle: ProjectHandle, new_file_path: str | Path) -> ProjectHandle:
    new_path = Path(new_file_path)
    if new_path.exists():
        raise FileExistsError(f"すでにファイルが存在します: {new_path}")

    save(handle)
    handle.connection.close()

    shutil.copyfile(handle.file_path, new_path)

    return open_project(new_path)
