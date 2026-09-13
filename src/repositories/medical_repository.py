from __future__ import annotations

import sqlite3

from models.medical import MedicalCriteria, MedicalCriteriaItem
from utils.uuid_utils import new_id


def get_by_project(conn: sqlite3.Connection, project_id: str) -> MedicalCriteria | None:
    row = conn.execute(
        "SELECT * FROM medical_criteria WHERE project_id = ?", (project_id,)
    ).fetchone()
    return _row_to_model(row) if row else None


def get_or_create(conn: sqlite3.Connection, project_id: str) -> MedicalCriteria:
    existing = get_by_project(conn, project_id)
    if existing is not None:
        return existing
    criteria = MedicalCriteria(medical_criteria_id=new_id(), project_id=project_id)
    conn.execute(
        "INSERT INTO medical_criteria (medical_criteria_id, project_id, immunity_performance_text) VALUES (?, ?, ?)",
        (criteria.medical_criteria_id, criteria.project_id, ""),
    )
    conn.commit()
    return criteria


def update(conn: sqlite3.Connection, criteria: MedicalCriteria) -> None:
    conn.execute(
        "UPDATE medical_criteria SET immunity_performance_text = ? WHERE medical_criteria_id = ?",
        (criteria.immunity_performance_text, criteria.medical_criteria_id),
    )
    conn.commit()


def list_items(conn: sqlite3.Connection, medical_criteria_id: str, category: str) -> list[MedicalCriteriaItem]:
    rows = conn.execute(
        "SELECT * FROM medical_criteria_items WHERE medical_criteria_id = ? AND category = ? ORDER BY sort_order",
        (medical_criteria_id, category),
    ).fetchall()
    return [
        MedicalCriteriaItem(
            item_id=row["item_id"],
            medical_criteria_id=row["medical_criteria_id"],
            category=row["category"],
            content=row["content"] or "",
            sort_order=row["sort_order"],
        )
        for row in rows
    ]


def replace_items(conn: sqlite3.Connection, medical_criteria_id: str, category: str, contents: list[str]) -> None:
    conn.execute(
        "DELETE FROM medical_criteria_items WHERE medical_criteria_id = ? AND category = ?",
        (medical_criteria_id, category),
    )
    for i, content in enumerate(contents):
        conn.execute(
            "INSERT INTO medical_criteria_items (item_id, medical_criteria_id, category, content, sort_order) VALUES (?, ?, ?, ?, ?)",
            (new_id(), medical_criteria_id, category, content, i),
        )
    conn.commit()


def _row_to_model(row: sqlite3.Row) -> MedicalCriteria:
    return MedicalCriteria(
        medical_criteria_id=row["medical_criteria_id"],
        project_id=row["project_id"],
        immunity_performance_text=row["immunity_performance_text"] or "",
    )
