from __future__ import annotations

import sqlite3

from models.operation_mode import OperationMode
from utils.uuid_utils import new_id


def list_by_project(conn: sqlite3.Connection, project_id: str) -> list[OperationMode]:
    rows = conn.execute(
        "SELECT * FROM operation_modes WHERE project_id = ? ORDER BY sort_order",
        (project_id,),
    ).fetchall()
    return [_row_to_model(row) for row in rows]


def add(conn: sqlite3.Connection, mode: OperationMode) -> OperationMode:
    if not mode.operation_mode_id:
        mode.operation_mode_id = new_id()
    conn.execute(
        """
        INSERT INTO operation_modes (operation_mode_id, project_id, mode_name, description, sort_order)
        VALUES (?, ?, ?, ?, ?)
        """,
        (mode.operation_mode_id, mode.project_id, mode.mode_name, mode.description, mode.sort_order),
    )
    conn.commit()
    return mode


def update(conn: sqlite3.Connection, mode: OperationMode) -> None:
    conn.execute(
        """
        UPDATE operation_modes SET mode_name = ?, description = ?, sort_order = ?
        WHERE operation_mode_id = ?
        """,
        (mode.mode_name, mode.description, mode.sort_order, mode.operation_mode_id),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, operation_mode_id: str) -> None:
    conn.execute("DELETE FROM operation_modes WHERE operation_mode_id = ?", (operation_mode_id,))
    conn.commit()


def _row_to_model(row: sqlite3.Row) -> OperationMode:
    return OperationMode(
        operation_mode_id=row["operation_mode_id"],
        project_id=row["project_id"],
        mode_name=row["mode_name"] or "",
        description=row["description"] or "",
        sort_order=row["sort_order"],
    )
