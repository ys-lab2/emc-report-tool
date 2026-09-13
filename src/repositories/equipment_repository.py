from __future__ import annotations

import sqlite3

from models.equipment import Equipment
from utils.time_utils import now_iso
from utils.uuid_utils import new_id


def list_by_project(conn: sqlite3.Connection, project_id: str) -> list[Equipment]:
    rows = conn.execute(
        "SELECT * FROM equipments WHERE project_id = ? ORDER BY sort_order",
        (project_id,),
    ).fetchall()
    return [_row_to_model(row) for row in rows]


def get(conn: sqlite3.Connection, equipment_id: str) -> Equipment | None:
    row = conn.execute(
        "SELECT * FROM equipments WHERE equipment_id = ?", (equipment_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_model(row)


def list_children(conn: sqlite3.Connection, parent_equipment_id: str) -> list[Equipment]:
    rows = conn.execute(
        "SELECT * FROM equipments WHERE parent_equipment_id = ? ORDER BY sort_order",
        (parent_equipment_id,),
    ).fetchall()
    return [_row_to_model(row) for row in rows]


def add(conn: sqlite3.Connection, equipment: Equipment) -> Equipment:
    if not equipment.equipment_id:
        equipment.equipment_id = new_id()
    timestamp = now_iso()
    equipment.created_at = timestamp
    equipment.updated_at = timestamp
    conn.execute(
        """
        INSERT INTO equipments
            (equipment_id, project_id, display_id, category, description, model_name,
             serial, manufacturer, fcc_id, bsmi_id, notes, placement_type,
             parent_equipment_id, sort_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            equipment.equipment_id,
            equipment.project_id,
            equipment.display_id,
            equipment.category,
            equipment.description,
            equipment.model_name,
            equipment.serial,
            equipment.manufacturer,
            equipment.fcc_id,
            equipment.bsmi_id,
            equipment.notes,
            equipment.placement_type,
            equipment.parent_equipment_id,
            equipment.sort_order,
            equipment.created_at,
            equipment.updated_at,
        ),
    )
    conn.commit()
    return equipment


def update(conn: sqlite3.Connection, equipment: Equipment) -> None:
    equipment.updated_at = now_iso()
    conn.execute(
        """
        UPDATE equipments SET
            display_id = ?, category = ?, description = ?, model_name = ?,
            serial = ?, manufacturer = ?, fcc_id = ?, bsmi_id = ?, notes = ?,
            placement_type = ?, parent_equipment_id = ?, sort_order = ?, updated_at = ?
        WHERE equipment_id = ?
        """,
        (
            equipment.display_id,
            equipment.category,
            equipment.description,
            equipment.model_name,
            equipment.serial,
            equipment.manufacturer,
            equipment.fcc_id,
            equipment.bsmi_id,
            equipment.notes,
            equipment.placement_type,
            equipment.parent_equipment_id,
            equipment.sort_order,
            equipment.updated_at,
            equipment.equipment_id,
        ),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, equipment_id: str) -> None:
    conn.execute("DELETE FROM equipments WHERE equipment_id = ?", (equipment_id,))
    conn.commit()


def clear_parent_for_children(conn: sqlite3.Connection, parent_equipment_id: str) -> None:
    """子機器を独立機器（standalone）に変更する。"""
    conn.execute(
        """
        UPDATE equipments SET parent_equipment_id = NULL, placement_type = 'standalone'
        WHERE parent_equipment_id = ?
        """,
        (parent_equipment_id,),
    )
    conn.commit()


def count_cables_referencing(conn: sqlite3.Connection, equipment_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM cables WHERE from_equipment_id = ? OR to_equipment_id = ?",
        (equipment_id, equipment_id),
    ).fetchone()
    return row["cnt"]


def _row_to_model(row: sqlite3.Row) -> Equipment:
    return Equipment(
        equipment_id=row["equipment_id"],
        project_id=row["project_id"],
        display_id=row["display_id"] or "",
        category=row["category"],
        description=row["description"] or "",
        model_name=row["model_name"] or "",
        serial=row["serial"] or "",
        manufacturer=row["manufacturer"] or "",
        fcc_id=row["fcc_id"] or "",
        bsmi_id=row["bsmi_id"] or "",
        notes=row["notes"] or "",
        placement_type=row["placement_type"],
        parent_equipment_id=row["parent_equipment_id"],
        sort_order=row["sort_order"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
