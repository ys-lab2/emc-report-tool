from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version     INTEGER PRIMARY KEY,
            applied_at  TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _applied_versions(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row["version"] for row in rows}


def _discover_migrations() -> list[tuple[int, Path]]:
    migrations = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        version_str = path.stem.split("_", 1)[0]
        migrations.append((int(version_str), path))
    return migrations


def apply_migrations(conn: sqlite3.Connection) -> list[int]:
    """未適用のマイグレーションを順に適用し、適用したバージョン番号一覧を返す。"""
    _ensure_migrations_table(conn)
    applied = _applied_versions(conn)
    newly_applied: list[int] = []

    for version, path in _discover_migrations():
        if version in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        logger.info("Applying migration %s (%s)", version, path.name)
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (version, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        newly_applied.append(version)

    return newly_applied
