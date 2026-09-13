from __future__ import annotations

import sqlite3

from models.ground_connection import GroundConnection
from utils.uuid_utils import new_id


def list_by_project(conn: sqlite3.Connection, project_id: str) -> list[GroundConnection]:
    rows = conn.execute(
        "SELECT * FROM ground_connections WHERE project_id = ?", (project_id,)
    ).fetchall()
    return [_row_to_model(row) for row in rows]


def get(conn: sqlite3.Connection, ground_connection_id: str) -> GroundConnection | None:
    row = conn.execute(
        "SELECT * FROM ground_connections WHERE ground_connection_id = ?", (ground_connection_id,)
    ).fetchone()
    return _row_to_model(row) if row else None


def add(conn: sqlite3.Connection, ground: GroundConnection) -> GroundConnection:
    if not ground.ground_connection_id:
        ground.ground_connection_id = new_id()
    conn.execute(
        "INSERT INTO ground_connections (ground_connection_id, project_id, kind, label, notes) VALUES (?, ?, ?, ?, ?)",
        (ground.ground_connection_id, ground.project_id, ground.kind, ground.label, ground.notes),
    )
    conn.commit()
    return ground


def update(conn: sqlite3.Connection, ground: GroundConnection) -> None:
    conn.execute(
        "UPDATE ground_connections SET kind = ?, label = ?, notes = ? WHERE ground_connection_id = ?",
        (ground.kind, ground.label, ground.notes, ground.ground_connection_id),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, ground_connection_id: str) -> None:
    conn.execute("DELETE FROM ground_connections WHERE ground_connection_id = ?", (ground_connection_id,))
    conn.commit()


def _row_to_model(row: sqlite3.Row) -> GroundConnection:
    return GroundConnection(
        ground_connection_id=row["ground_connection_id"],
        project_id=row["project_id"],
        kind=row["kind"],
        label=row["label"] or "",
        notes=row["notes"] or "",
    )
