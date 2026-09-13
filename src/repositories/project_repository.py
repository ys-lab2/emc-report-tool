from __future__ import annotations

import sqlite3

from models.project import Project


def insert(conn: sqlite3.Connection, project: Project) -> None:
    conn.execute(
        """
        INSERT INTO projects
            (project_id, project_no, test_plan_no, measurement_period,
             include_immunity, include_medical, include_taiwan, notes,
             created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project.project_id,
            project.project_no,
            project.test_plan_no,
            project.measurement_period,
            int(project.include_immunity),
            int(project.include_medical),
            int(project.include_taiwan),
            project.notes,
            project.created_at,
            project.updated_at,
        ),
    )
    conn.commit()


def update(conn: sqlite3.Connection, project: Project) -> None:
    conn.execute(
        """
        UPDATE projects SET
            project_no = ?, test_plan_no = ?, measurement_period = ?,
            include_immunity = ?, include_medical = ?, include_taiwan = ?,
            notes = ?, updated_at = ?
        WHERE project_id = ?
        """,
        (
            project.project_no,
            project.test_plan_no,
            project.measurement_period,
            int(project.include_immunity),
            int(project.include_medical),
            int(project.include_taiwan),
            project.notes,
            project.updated_at,
            project.project_id,
        ),
    )
    conn.commit()


def get(conn: sqlite3.Connection, project_id: str) -> Project | None:
    row = conn.execute(
        "SELECT * FROM projects WHERE project_id = ?", (project_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_project(row)


def get_first(conn: sqlite3.Connection) -> Project | None:
    row = conn.execute("SELECT * FROM projects LIMIT 1").fetchone()
    if row is None:
        return None
    return _row_to_project(row)


def _row_to_project(row: sqlite3.Row) -> Project:
    return Project(
        project_id=row["project_id"],
        project_no=row["project_no"] or "",
        test_plan_no=row["test_plan_no"] or "",
        measurement_period=row["measurement_period"] or "",
        include_immunity=bool(row["include_immunity"]),
        include_medical=bool(row["include_medical"]),
        include_taiwan=bool(row["include_taiwan"]),
        notes=row["notes"] or "",
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
