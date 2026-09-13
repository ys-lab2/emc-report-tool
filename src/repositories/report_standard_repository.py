from __future__ import annotations

import sqlite3

from models.report_standard import ReportStandard
from utils.uuid_utils import new_id


def list_by_project(conn: sqlite3.Connection, project_id: str) -> list[ReportStandard]:
    rows = conn.execute(
        "SELECT * FROM report_standards WHERE project_id = ? ORDER BY sort_order",
        (project_id,),
    ).fetchall()
    return [_row_to_model(row) for row in rows]


def add(conn: sqlite3.Connection, standard: ReportStandard) -> ReportStandard:
    if not standard.report_standard_id:
        standard.report_standard_id = new_id()
    conn.execute(
        """
        INSERT INTO report_standards
            (report_standard_id, project_id, standard_name, language,
             desired_due_date, submission_media, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            standard.report_standard_id,
            standard.project_id,
            standard.standard_name,
            standard.language,
            standard.desired_due_date,
            standard.submission_media,
            standard.sort_order,
        ),
    )
    conn.commit()
    return standard


def update(conn: sqlite3.Connection, standard: ReportStandard) -> None:
    conn.execute(
        """
        UPDATE report_standards SET
            standard_name = ?, language = ?, desired_due_date = ?,
            submission_media = ?, sort_order = ?
        WHERE report_standard_id = ?
        """,
        (
            standard.standard_name,
            standard.language,
            standard.desired_due_date,
            standard.submission_media,
            standard.sort_order,
            standard.report_standard_id,
        ),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, report_standard_id: str) -> None:
    conn.execute(
        "DELETE FROM report_standards WHERE report_standard_id = ?",
        (report_standard_id,),
    )
    conn.commit()


def _row_to_model(row: sqlite3.Row) -> ReportStandard:
    return ReportStandard(
        report_standard_id=row["report_standard_id"],
        project_id=row["project_id"],
        standard_name=row["standard_name"] or "",
        language=row["language"] or "jp",
        desired_due_date=row["desired_due_date"] or "",
        submission_media=row["submission_media"] or "PDF",
        sort_order=row["sort_order"],
    )
