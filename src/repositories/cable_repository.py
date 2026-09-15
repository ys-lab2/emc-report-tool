from __future__ import annotations

import sqlite3

from models.cable import Cable
from utils.time_utils import now_iso
from utils.uuid_utils import new_id


def list_by_project(conn: sqlite3.Connection, project_id: str) -> list[Cable]:
    rows = conn.execute(
        "SELECT * FROM cables WHERE project_id = ? ORDER BY cable_no",
        (project_id,),
    ).fetchall()
    return [_row_to_model(row) for row in rows]


def get(conn: sqlite3.Connection, cable_id: str) -> Cable | None:
    row = conn.execute(
        "SELECT * FROM cables WHERE cable_id = ?", (cable_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_model(row)


def add(conn: sqlite3.Connection, cable: Cable) -> Cable:
    if not cable.cable_id:
        cable.cable_id = new_id()
    timestamp = now_iso()
    cable.created_at = timestamp
    cable.updated_at = timestamp
    conn.execute(
        """
        INSERT INTO cables
            (cable_id, project_id, cable_no, from_ref_type, from_ref_id, from_port,
             to_ref_type, to_ref_id, to_port, cable_type, length, length_unit,
             shielded, maximum_length, outdoor_connection, notes, sort_order,
             created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cable.cable_id,
            cable.project_id,
            cable.cable_no,
            cable.from_ref_type,
            cable.from_ref_id,
            cable.from_port,
            cable.to_ref_type,
            cable.to_ref_id,
            cable.to_port,
            cable.cable_type,
            cable.length,
            cable.length_unit,
            cable.shielded,
            cable.maximum_length,
            cable.outdoor_connection,
            cable.notes,
            cable.sort_order,
            cable.created_at,
            cable.updated_at,
        ),
    )
    conn.commit()
    return cable


def update(conn: sqlite3.Connection, cable: Cable) -> None:
    cable.updated_at = now_iso()
    conn.execute(
        """
        UPDATE cables SET
            cable_no = ?, from_ref_type = ?, from_ref_id = ?, from_port = ?,
            to_ref_type = ?, to_ref_id = ?, to_port = ?, cable_type = ?, length = ?,
            length_unit = ?, shielded = ?, maximum_length = ?, outdoor_connection = ?,
            notes = ?, sort_order = ?, updated_at = ?
        WHERE cable_id = ?
        """,
        (
            cable.cable_no,
            cable.from_ref_type,
            cable.from_ref_id,
            cable.from_port,
            cable.to_ref_type,
            cable.to_ref_id,
            cable.to_port,
            cable.cable_type,
            cable.length,
            cable.length_unit,
            cable.shielded,
            cable.maximum_length,
            cable.outdoor_connection,
            cable.notes,
            cable.sort_order,
            cable.updated_at,
            cable.cable_id,
        ),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, cable_id: str) -> None:
    conn.execute("DELETE FROM cables WHERE cable_id = ?", (cable_id,))
    conn.commit()


def delete_by_ref(conn: sqlite3.Connection, ref_type: str, ref_id: str) -> None:
    """指定した機器/電源/GNDが片端になっているケーブルを一括削除する
    （from/toの多態的参照にはDB外部キー制約が使えないため、Service層で明示的にカスケードする）。"""
    conn.execute(
        """
        DELETE FROM cables
        WHERE (from_ref_type = ? AND from_ref_id = ?)
           OR (to_ref_type = ? AND to_ref_id = ?)
        """,
        (ref_type, ref_id, ref_type, ref_id),
    )
    conn.commit()


def next_cable_no(conn: sqlite3.Connection, project_id: str) -> int:
    row = conn.execute(
        "SELECT MAX(cable_no) AS max_no FROM cables WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    return (row["max_no"] or 0) + 1


def _row_to_model(row: sqlite3.Row) -> Cable:
    return Cable(
        cable_id=row["cable_id"],
        project_id=row["project_id"],
        cable_no=row["cable_no"],
        from_ref_type=row["from_ref_type"],
        from_ref_id=row["from_ref_id"],
        from_port=row["from_port"] or "",
        to_ref_type=row["to_ref_type"],
        to_ref_id=row["to_ref_id"],
        to_port=row["to_port"] or "",
        cable_type=row["cable_type"] or "",
        length=row["length"],
        length_unit=row["length_unit"] or "m",
        shielded=row["shielded"] or "unknown",
        maximum_length=row["maximum_length"] or "",
        outdoor_connection=row["outdoor_connection"] or "unknown",
        notes=row["notes"] or "",
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
