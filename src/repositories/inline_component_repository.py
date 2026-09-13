from __future__ import annotations

import sqlite3

from models.inline_component import InlineComponent
from utils.uuid_utils import new_id


def list_by_cable(conn: sqlite3.Connection, cable_id: str) -> list[InlineComponent]:
    rows = conn.execute(
        "SELECT * FROM inline_components WHERE cable_id = ? ORDER BY sort_order",
        (cable_id,),
    ).fetchall()
    return [_row_to_model(row) for row in rows]


def add(conn: sqlite3.Connection, component: InlineComponent) -> InlineComponent:
    if not component.inline_component_id:
        component.inline_component_id = new_id()
    conn.execute(
        """
        INSERT INTO inline_components
            (inline_component_id, cable_id, type, name, model, manufacturer,
             quantity, position, notes, countermeasure_id, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            component.inline_component_id,
            component.cable_id,
            component.type,
            component.name,
            component.model,
            component.manufacturer,
            component.quantity,
            component.position,
            component.notes,
            component.countermeasure_id,
            component.sort_order,
        ),
    )
    conn.commit()
    return component


def update(conn: sqlite3.Connection, component: InlineComponent) -> None:
    conn.execute(
        """
        UPDATE inline_components SET
            type = ?, name = ?, model = ?, manufacturer = ?, quantity = ?,
            position = ?, notes = ?, countermeasure_id = ?, sort_order = ?
        WHERE inline_component_id = ?
        """,
        (
            component.type,
            component.name,
            component.model,
            component.manufacturer,
            component.quantity,
            component.position,
            component.notes,
            component.countermeasure_id,
            component.sort_order,
            component.inline_component_id,
        ),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, inline_component_id: str) -> None:
    conn.execute(
        "DELETE FROM inline_components WHERE inline_component_id = ?",
        (inline_component_id,),
    )
    conn.commit()


def _row_to_model(row: sqlite3.Row) -> InlineComponent:
    return InlineComponent(
        inline_component_id=row["inline_component_id"],
        cable_id=row["cable_id"],
        type=row["type"],
        name=row["name"] or "",
        model=row["model"] or "",
        manufacturer=row["manufacturer"] or "",
        quantity=row["quantity"],
        position=row["position"] or "Middle",
        notes=row["notes"] or "",
        countermeasure_id=row["countermeasure_id"],
        sort_order=row["sort_order"],
    )
