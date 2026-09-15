from __future__ import annotations

import sqlite3

from models.power_source import PowerSource
from utils.uuid_utils import new_id


def list_by_project(conn: sqlite3.Connection, project_id: str) -> list[PowerSource]:
    rows = conn.execute(
        "SELECT * FROM power_sources WHERE project_id = ?", (project_id,)
    ).fetchall()
    return [_row_to_model(row) for row in rows]


def get(conn: sqlite3.Connection, power_source_id: str) -> PowerSource | None:
    row = conn.execute(
        "SELECT * FROM power_sources WHERE power_source_id = ?", (power_source_id,)
    ).fetchone()
    return _row_to_model(row) if row else None


def add(conn: sqlite3.Connection, power_source: PowerSource) -> PowerSource:
    if not power_source.power_source_id:
        power_source.power_source_id = new_id()
    conn.execute(
        """
        INSERT INTO power_sources (power_source_id, project_id, kind, label, notes, frequency_hz, test_voltage)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            power_source.power_source_id,
            power_source.project_id,
            power_source.kind,
            power_source.label,
            power_source.notes,
            power_source.frequency_hz,
            power_source.test_voltage,
        ),
    )
    conn.commit()
    return power_source


def update(conn: sqlite3.Connection, power_source: PowerSource) -> None:
    conn.execute(
        """
        UPDATE power_sources SET kind = ?, label = ?, notes = ?, frequency_hz = ?, test_voltage = ?
        WHERE power_source_id = ?
        """,
        (
            power_source.kind,
            power_source.label,
            power_source.notes,
            power_source.frequency_hz,
            power_source.test_voltage,
            power_source.power_source_id,
        ),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, power_source_id: str) -> None:
    conn.execute("DELETE FROM power_sources WHERE power_source_id = ?", (power_source_id,))
    conn.commit()


def _row_to_model(row: sqlite3.Row) -> PowerSource:
    return PowerSource(
        power_source_id=row["power_source_id"],
        project_id=row["project_id"],
        kind=row["kind"],
        label=row["label"] or "",
        notes=row["notes"] or "",
        frequency_hz=row["frequency_hz"] or "",
        test_voltage=row["test_voltage"] or "",
    )
