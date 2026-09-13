from __future__ import annotations

import sqlite3

from models.countermeasure import Countermeasure
from utils.uuid_utils import new_id


def list_by_project(conn: sqlite3.Connection, project_id: str) -> list[Countermeasure]:
    rows = conn.execute(
        "SELECT * FROM countermeasures WHERE project_id = ? ORDER BY sort_order",
        (project_id,),
    ).fetchall()
    return [_row_to_model(row) for row in rows]


def add(conn: sqlite3.Connection, item: Countermeasure) -> Countermeasure:
    if not item.countermeasure_id:
        item.countermeasure_id = new_id()
    conn.execute(
        """
        INSERT INTO countermeasures
            (countermeasure_id, project_id, description, component_model, component_manufacturer, sort_order)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (item.countermeasure_id, item.project_id, item.description, item.component_model, item.component_manufacturer, item.sort_order),
    )
    conn.commit()
    return item


def update(conn: sqlite3.Connection, item: Countermeasure) -> None:
    conn.execute(
        """
        UPDATE countermeasures SET
            description = ?, component_model = ?, component_manufacturer = ?, sort_order = ?
        WHERE countermeasure_id = ?
        """,
        (item.description, item.component_model, item.component_manufacturer, item.sort_order, item.countermeasure_id),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, countermeasure_id: str) -> None:
    conn.execute("DELETE FROM countermeasures WHERE countermeasure_id = ?", (countermeasure_id,))
    conn.commit()


def _row_to_model(row: sqlite3.Row) -> Countermeasure:
    return Countermeasure(
        countermeasure_id=row["countermeasure_id"],
        project_id=row["project_id"],
        description=row["description"] or "",
        component_model=row["component_model"] or "",
        component_manufacturer=row["component_manufacturer"] or "",
        sort_order=row["sort_order"],
    )
