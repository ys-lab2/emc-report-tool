from __future__ import annotations

import sqlite3

from models.taiwan import InternalComponent, TaiwanApplicant
from utils.uuid_utils import new_id


def get_by_project(conn: sqlite3.Connection, project_id: str) -> TaiwanApplicant | None:
    row = conn.execute(
        "SELECT * FROM taiwan_applicants WHERE project_id = ?", (project_id,)
    ).fetchone()
    return _row_to_model(row) if row else None


def get_or_create(conn: sqlite3.Connection, project_id: str) -> TaiwanApplicant:
    existing = get_by_project(conn, project_id)
    if existing is not None:
        return existing
    applicant = TaiwanApplicant(taiwan_applicant_id=new_id(), project_id=project_id)
    conn.execute(
        """
        INSERT INTO taiwan_applicants
            (taiwan_applicant_id, project_id, company_name_en, address_en, company_name_zh, address_zh, notes, eut_operation_status_text)
        VALUES (?, ?, '', '', '', '', '', '')
        """,
        (applicant.taiwan_applicant_id, applicant.project_id),
    )
    conn.commit()
    return applicant


def update(conn: sqlite3.Connection, applicant: TaiwanApplicant) -> None:
    conn.execute(
        """
        UPDATE taiwan_applicants SET
            company_name_en = ?, address_en = ?, company_name_zh = ?, address_zh = ?,
            notes = ?, eut_operation_status_text = ?
        WHERE taiwan_applicant_id = ?
        """,
        (
            applicant.company_name_en,
            applicant.address_en,
            applicant.company_name_zh,
            applicant.address_zh,
            applicant.notes,
            applicant.eut_operation_status_text,
            applicant.taiwan_applicant_id,
        ),
    )
    conn.commit()


def list_internal_components(conn: sqlite3.Connection, taiwan_applicant_id: str) -> list[InternalComponent]:
    rows = conn.execute(
        "SELECT * FROM internal_components WHERE taiwan_applicant_id = ? ORDER BY sort_order",
        (taiwan_applicant_id,),
    ).fetchall()
    return [_row_to_component(row) for row in rows]


def add_internal_component(conn: sqlite3.Connection, component: InternalComponent) -> InternalComponent:
    if not component.internal_component_id:
        component.internal_component_id = new_id()
    conn.execute(
        """
        INSERT INTO internal_components
            (internal_component_id, taiwan_applicant_id, device_name, quantity_max, model_name, manufacturer, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            component.internal_component_id,
            component.taiwan_applicant_id,
            component.device_name,
            component.quantity_max,
            component.model_name,
            component.manufacturer,
            component.sort_order,
        ),
    )
    conn.commit()
    return component


def update_internal_component(conn: sqlite3.Connection, component: InternalComponent) -> None:
    conn.execute(
        """
        UPDATE internal_components SET
            device_name = ?, quantity_max = ?, model_name = ?, manufacturer = ?, sort_order = ?
        WHERE internal_component_id = ?
        """,
        (
            component.device_name,
            component.quantity_max,
            component.model_name,
            component.manufacturer,
            component.sort_order,
            component.internal_component_id,
        ),
    )
    conn.commit()


def delete_internal_component(conn: sqlite3.Connection, internal_component_id: str) -> None:
    conn.execute("DELETE FROM internal_components WHERE internal_component_id = ?", (internal_component_id,))
    conn.commit()


def _row_to_model(row: sqlite3.Row) -> TaiwanApplicant:
    return TaiwanApplicant(
        taiwan_applicant_id=row["taiwan_applicant_id"],
        project_id=row["project_id"],
        company_name_en=row["company_name_en"] or "",
        address_en=row["address_en"] or "",
        company_name_zh=row["company_name_zh"] or "",
        address_zh=row["address_zh"] or "",
        notes=row["notes"] or "",
        eut_operation_status_text=row["eut_operation_status_text"] or "",
    )


def _row_to_component(row: sqlite3.Row) -> InternalComponent:
    return InternalComponent(
        internal_component_id=row["internal_component_id"],
        taiwan_applicant_id=row["taiwan_applicant_id"],
        device_name=row["device_name"] or "",
        quantity_max=row["quantity_max"] or "",
        model_name=row["model_name"] or "",
        manufacturer=row["manufacturer"] or "",
        sort_order=row["sort_order"],
    )
