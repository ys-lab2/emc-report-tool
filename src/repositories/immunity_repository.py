from __future__ import annotations

import sqlite3

from models.immunity import ImmunityCriteria, ImmunityVerificationPoint
from utils.uuid_utils import new_id


def get_by_project(conn: sqlite3.Connection, project_id: str) -> ImmunityCriteria | None:
    row = conn.execute(
        "SELECT * FROM immunity_criteria WHERE project_id = ?", (project_id,)
    ).fetchone()
    return _row_to_model(row) if row else None


def get_or_create(conn: sqlite3.Connection, project_id: str) -> ImmunityCriteria:
    existing = get_by_project(conn, project_id)
    if existing is not None:
        return existing
    criteria = ImmunityCriteria(immunity_criteria_id=new_id(), project_id=project_id)
    conn.execute(
        "INSERT INTO immunity_criteria (immunity_criteria_id, project_id, criterion_a, criterion_b, criterion_c) VALUES (?, ?, ?, ?, ?)",
        (criteria.immunity_criteria_id, criteria.project_id, "", "", ""),
    )
    conn.commit()
    return criteria


def update(conn: sqlite3.Connection, criteria: ImmunityCriteria) -> None:
    conn.execute(
        "UPDATE immunity_criteria SET criterion_a = ?, criterion_b = ?, criterion_c = ? WHERE immunity_criteria_id = ?",
        (criteria.criterion_a, criteria.criterion_b, criteria.criterion_c, criteria.immunity_criteria_id),
    )
    conn.commit()


def list_verification_points(conn: sqlite3.Connection, immunity_criteria_id: str) -> list[ImmunityVerificationPoint]:
    rows = conn.execute(
        "SELECT * FROM immunity_verification_points WHERE immunity_criteria_id = ? ORDER BY sort_order",
        (immunity_criteria_id,),
    ).fetchall()
    return [
        ImmunityVerificationPoint(
            point_id=row["point_id"],
            immunity_criteria_id=row["immunity_criteria_id"],
            content=row["content"] or "",
            sort_order=row["sort_order"],
        )
        for row in rows
    ]


def replace_verification_points(conn: sqlite3.Connection, immunity_criteria_id: str, contents: list[str]) -> None:
    """自由記述のテキストエリアを改行区切りで丸ごと保存し直す（フリーライティング方式）。"""
    conn.execute(
        "DELETE FROM immunity_verification_points WHERE immunity_criteria_id = ?", (immunity_criteria_id,)
    )
    for i, content in enumerate(contents):
        conn.execute(
            "INSERT INTO immunity_verification_points (point_id, immunity_criteria_id, content, sort_order) VALUES (?, ?, ?, ?)",
            (new_id(), immunity_criteria_id, content, i),
        )
    conn.commit()


def _row_to_model(row: sqlite3.Row) -> ImmunityCriteria:
    return ImmunityCriteria(
        immunity_criteria_id=row["immunity_criteria_id"],
        project_id=row["project_id"],
        criterion_a=row["criterion_a"] or "",
        criterion_b=row["criterion_b"] or "",
        criterion_c=row["criterion_c"] or "",
    )
