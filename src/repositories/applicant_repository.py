from __future__ import annotations

import sqlite3

from models.applicant import Applicant
from utils.uuid_utils import new_id


def get_by_project(conn: sqlite3.Connection, project_id: str) -> Applicant | None:
    row = conn.execute(
        "SELECT * FROM applicants WHERE project_id = ?", (project_id,)
    ).fetchone()
    if row is None:
        return None
    return Applicant(
        applicant_id=row["applicant_id"],
        project_id=row["project_id"],
        company_name_jp=row["company_name_jp"] or "",
        company_name_en=row["company_name_en"] or "",
        address_jp=row["address_jp"] or "",
        address_en=row["address_en"] or "",
        notes=row["notes"] or "",
    )


def upsert(conn: sqlite3.Connection, applicant: Applicant) -> Applicant:
    """project_idにつき1件（Project 1:1）。存在すれば更新、無ければ新規作成する。"""
    existing = get_by_project(conn, applicant.project_id)
    if existing is None:
        if not applicant.applicant_id:
            applicant.applicant_id = new_id()
        conn.execute(
            """
            INSERT INTO applicants
                (applicant_id, project_id, company_name_jp, company_name_en,
                 address_jp, address_en, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                applicant.applicant_id,
                applicant.project_id,
                applicant.company_name_jp,
                applicant.company_name_en,
                applicant.address_jp,
                applicant.address_en,
                applicant.notes,
            ),
        )
    else:
        applicant.applicant_id = existing.applicant_id
        conn.execute(
            """
            UPDATE applicants SET
                company_name_jp = ?, company_name_en = ?,
                address_jp = ?, address_en = ?, notes = ?
            WHERE applicant_id = ?
            """,
            (
                applicant.company_name_jp,
                applicant.company_name_en,
                applicant.address_jp,
                applicant.address_en,
                applicant.notes,
                applicant.applicant_id,
            ),
        )
    conn.commit()
    return applicant
