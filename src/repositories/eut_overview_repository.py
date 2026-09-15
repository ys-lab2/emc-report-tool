from __future__ import annotations

import json
import sqlite3

from models.eut_overview import EutOverview, Frequency
from utils.uuid_utils import new_id


def get_by_project(conn: sqlite3.Connection, project_id: str) -> EutOverview | None:
    row = conn.execute(
        "SELECT * FROM eut_overviews WHERE project_id = ?", (project_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_model(row)


def upsert(conn: sqlite3.Connection, overview: EutOverview) -> EutOverview:
    existing = get_by_project(conn, overview.project_id)
    power_types_json = json.dumps(overview.rating_power_supply_types)
    # sample_typeは未選択(空文字列)を許容するチェックボックス項目のため、CHECK制約に
    # 引っかからないようDB上はNULLとして保存する（58.節：未確定状態での保存を許容）。
    sample_type = overview.sample_type or None

    if existing is None:
        if not overview.eut_overview_id:
            overview.eut_overview_id = new_id()
        conn.execute(
            """
            INSERT INTO eut_overviews
                (eut_overview_id, project_id, kind_of_equipment, model_name, serial_no,
                 operating_program, sample_type, width_mm, depth_mm, height_mm,
                 max_frequency, wireless_frequency, rating_power_supply_types,
                 rating_power_supply_value, tested_condition, date_of_manufacture,
                 manufacturer_name, manufacturer_address, attachment, option,
                 date_sample_received, test_engineer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                overview.eut_overview_id,
                overview.project_id,
                overview.kind_of_equipment,
                overview.model_name,
                overview.serial_no,
                overview.operating_program,
                sample_type,
                overview.width_mm,
                overview.depth_mm,
                overview.height_mm,
                overview.max_frequency,
                overview.wireless_frequency,
                power_types_json,
                overview.rating_power_supply_value,
                overview.tested_condition,
                overview.date_of_manufacture,
                overview.manufacturer_name,
                overview.manufacturer_address,
                overview.attachment,
                overview.option,
                overview.date_sample_received,
                overview.test_engineer,
            ),
        )
    else:
        overview.eut_overview_id = existing.eut_overview_id
        conn.execute(
            """
            UPDATE eut_overviews SET
                kind_of_equipment = ?, model_name = ?, serial_no = ?,
                operating_program = ?, sample_type = ?, width_mm = ?, depth_mm = ?,
                height_mm = ?, max_frequency = ?, wireless_frequency = ?,
                rating_power_supply_types = ?, rating_power_supply_value = ?,
                tested_condition = ?, date_of_manufacture = ?, manufacturer_name = ?,
                manufacturer_address = ?, attachment = ?, option = ?,
                date_sample_received = ?, test_engineer = ?
            WHERE eut_overview_id = ?
            """,
            (
                overview.kind_of_equipment,
                overview.model_name,
                overview.serial_no,
                overview.operating_program,
                sample_type,
                overview.width_mm,
                overview.depth_mm,
                overview.height_mm,
                overview.max_frequency,
                overview.wireless_frequency,
                power_types_json,
                overview.rating_power_supply_value,
                overview.tested_condition,
                overview.date_of_manufacture,
                overview.manufacturer_name,
                overview.manufacturer_address,
                overview.attachment,
                overview.option,
                overview.date_sample_received,
                overview.test_engineer,
                overview.eut_overview_id,
            ),
        )
    conn.commit()
    return overview


def _row_to_model(row: sqlite3.Row) -> EutOverview:
    raw_types = row["rating_power_supply_types"]
    power_types = json.loads(raw_types) if raw_types else []
    return EutOverview(
        eut_overview_id=row["eut_overview_id"],
        project_id=row["project_id"],
        kind_of_equipment=row["kind_of_equipment"] or "",
        model_name=row["model_name"] or "",
        serial_no=row["serial_no"] or "",
        operating_program=row["operating_program"] or "",
        sample_type=row["sample_type"] or "",
        width_mm=row["width_mm"],
        depth_mm=row["depth_mm"],
        height_mm=row["height_mm"],
        max_frequency=row["max_frequency"] or "",
        wireless_frequency=row["wireless_frequency"] or "",
        rating_power_supply_types=power_types,
        rating_power_supply_value=row["rating_power_supply_value"] or "",
        tested_condition=row["tested_condition"] or "",
        date_of_manufacture=row["date_of_manufacture"] or "",
        manufacturer_name=row["manufacturer_name"] or "",
        manufacturer_address=row["manufacturer_address"] or "",
        attachment=row["attachment"] or "",
        option=row["option"] or "",
        date_sample_received=row["date_sample_received"] or "",
        test_engineer=row["test_engineer"] or "",
    )


def list_frequencies(conn: sqlite3.Connection, eut_overview_id: str) -> list[Frequency]:
    rows = conn.execute(
        "SELECT * FROM frequencies WHERE eut_overview_id = ? ORDER BY sort_order",
        (eut_overview_id,),
    ).fetchall()
    return [
        Frequency(
            frequency_id=row["frequency_id"],
            eut_overview_id=row["eut_overview_id"],
            value=row["value"] or "",
            unit=row["unit"] or "",
            usage_note=row["usage_note"] or "",
            sort_order=row["sort_order"],
        )
        for row in rows
    ]


def add_frequency(conn: sqlite3.Connection, frequency: Frequency) -> Frequency:
    if not frequency.frequency_id:
        frequency.frequency_id = new_id()
    conn.execute(
        """
        INSERT INTO frequencies (frequency_id, eut_overview_id, value, unit, usage_note, sort_order)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            frequency.frequency_id,
            frequency.eut_overview_id,
            frequency.value,
            frequency.unit,
            frequency.usage_note,
            frequency.sort_order,
        ),
    )
    conn.commit()
    return frequency


def update_frequency(conn: sqlite3.Connection, frequency: Frequency) -> None:
    conn.execute(
        "UPDATE frequencies SET value = ?, unit = ?, usage_note = ?, sort_order = ? WHERE frequency_id = ?",
        (frequency.value, frequency.unit, frequency.usage_note, frequency.sort_order, frequency.frequency_id),
    )
    conn.commit()


def delete_frequency(conn: sqlite3.Connection, frequency_id: str) -> None:
    conn.execute("DELETE FROM frequencies WHERE frequency_id = ?", (frequency_id,))
    conn.commit()
