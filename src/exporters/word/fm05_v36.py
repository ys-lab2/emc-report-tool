"""MM-QR-001/FM05 (ファイル名バージョン Ver.3-6) 用のWord Exporter。

セル位置の根拠は docs/word-template-analysis.md 9A.節（Word COM実測結果）を参照。
テンプレートが改版された場合はこのファイルを新しいバージョン別ファイルとして複製し、
アプリ本体・データモデルには影響を与えないこと（8.節の方針）。
"""

from __future__ import annotations

from pathlib import Path

from exporters.word.base import (
    append_cell_text,
    copy_template,
    ensure_row_capacity,
    insert_picture_replacing_cell,
    set_cell_text,
    set_checkbox,
    word_application,
)
from models.cable import Cable
from models.equipment import Equipment
from models.eut_overview import EutOverview
from models.report_standard import ReportStandard
from repositories import (
    cable_repository,
    equipment_repository,
    eut_overview_repository,
    report_standard_repository,
)
from services.project_service import ProjectHandle

TEMPLATE_ID = "MM-QR-001/FM05"
TEMPLATE_VERSION = "3-6"

# --- Table(1): プロジェクト情報 ---
PROJECT_TABLE = 1

# --- Table(3): レポート作成規格 ---
STANDARDS_TABLE = 3
STANDARDS_START_ROW = 3
STANDARDS_CAPACITY = 8

# --- Table(4): 装置概要 ---
EUT_TABLE = 4
EUT_ROWS = {
    "kind_of_equipment": 2,
    "model_name": 3,
    "serial_no": 5,
    "operating_program": 6,
    "sample_type": 8,
    "dimension": 9,
    "max_frequency": 10,
    "wireless_frequency": 12,
    "rating_power_supply": 13,
    "tested_condition": 14,
    "date_of_manufacture": 15,
    "manufacturer_name": 16,
    "manufacturer_address": 17,
    "attachment": 18,
    "option": 19,
    "date_sample_received": 23,
    "test_engineer": 24,
}

CHECKBOX_INDEX = {
    "mass_production": 1,
    "pre_production": 2,
    "dc_overall": 3,
    "dc_2p": 4,
    "dc_2p_e": 5,
    "single_phase_overall": 6,
    "single_phase_2p": 7,
    "single_phase_2p_e": 8,
    "three_phase_overall": 9,
    "three_phase_3p_e": 10,
    "three_phase_4p_e": 11,
}

# --- Table(5): 機器リスト ---
EQUIPMENT_TABLE = 5
EQUIPMENT_SECTIONS = {
    "EUT": {"start_row": 4, "capacity": 3},
    "Peripheral": {"start_row": 8, "capacity": 6},
    "AssociatedEquipment": {"start_row": 15, "capacity": 5},
}
EQUIPMENT_COLUMNS = {
    "display_id": 1,
    "description": 2,
    "model_name": 3,
    "serial": 4,
    "manufacturer": 5,
    "fcc_bsmi": 6,
}

# --- Table(6): ケーブルリスト ---
CABLE_TABLE = 6
CABLE_START_ROW = 4
CABLE_CAPACITY = 14
CABLE_COLUMNS = {
    "cable_no": 1,
    "cable_type": 2,
    "length": 3,
    "shielded": 4,
    "maximum_length": 5,
    "outdoor_connection": 6,
}

# --- Table(7): 構成図 ---
DIAGRAM_TABLE = 7
DIAGRAM_ROW = 2
DIAGRAM_COL = 1

SHIELDED_LABELS = {"shielded": "Shielded", "non_shielded": "Non-shielded", "unknown": ""}
OUTDOOR_LABELS = {"yes": "する", "no": "しない", "unknown": ""}


def export(
    handle: ProjectHandle,
    template_path: Path,
    output_path: Path,
    diagram_image_path: Path | None = None,
) -> Path:
    conn = handle.connection
    project = handle.project

    copy_template(template_path, output_path)

    with word_application(visible=False) as word:
        doc = word.Documents.Open(str(output_path))
        try:
            _write_project_info(doc, project)
            _write_report_standards(conn, doc, project.project_id)
            _write_eut_overview(conn, doc, project.project_id)
            _write_equipment_table(conn, doc, project.project_id)
            _write_cable_table(conn, doc, project.project_id)
            if diagram_image_path is not None:
                _write_diagram(doc, diagram_image_path)
        finally:
            doc.Save()
            doc.Close(False)

    return output_path


def _write_project_info(doc, project) -> None:
    table = doc.Tables(PROJECT_TABLE)
    set_cell_text(table, 1, 2, project.project_no)
    set_cell_text(table, 2, 2, project.test_plan_no)
    set_cell_text(table, 3, 2, project.measurement_period)


def _write_report_standards(conn, doc, project_id: str) -> None:
    standards = report_standard_repository.list_by_project(conn, project_id)
    if not standards:
        return

    table = doc.Tables(STANDARDS_TABLE)
    ensure_row_capacity(table, STANDARDS_START_ROW, STANDARDS_CAPACITY, len(standards))

    language_label = {"jp": "和文", "en": "英文"}
    for i, standard in enumerate(standards):
        row = STANDARDS_START_ROW + i
        set_cell_text(table, row, 3, standard.standard_name)
        set_cell_text(table, row, 4, language_label.get(standard.language, standard.language))
        set_cell_text(table, row, 5, standard.desired_due_date)
        set_cell_text(table, row, 6, standard.submission_media)


def _write_eut_overview(conn, doc, project_id: str) -> None:
    overview = eut_overview_repository.get_by_project(conn, project_id)
    if overview is None:
        return

    table = doc.Tables(EUT_TABLE)

    set_cell_text(table, EUT_ROWS["kind_of_equipment"], 3, overview.kind_of_equipment)
    set_cell_text(table, EUT_ROWS["model_name"], 3, overview.model_name)
    set_cell_text(table, EUT_ROWS["serial_no"], 3, overview.serial_no)
    set_cell_text(table, EUT_ROWS["operating_program"], 3, overview.operating_program)

    set_checkbox(doc, CHECKBOX_INDEX["mass_production"], overview.sample_type == "mass_production")
    set_checkbox(doc, CHECKBOX_INDEX["pre_production"], overview.sample_type == "pre_production")

    if overview.width_mm or overview.depth_mm or overview.height_mm:
        dimension_text = (
            f"Width:{_fmt_num(overview.width_mm)}mm  "
            f"Depth:{_fmt_num(overview.depth_mm)}mm  "
            f"Height:{_fmt_num(overview.height_mm)}mm"
        )
        set_cell_text(table, EUT_ROWS["dimension"], 3, dimension_text)

    append_cell_text(table, EUT_ROWS["max_frequency"], 3, overview.max_frequency)
    set_cell_text(table, EUT_ROWS["wireless_frequency"], 3, overview.wireless_frequency)

    _write_power_supply_checkboxes(doc, overview)
    if overview.rating_power_supply_value:
        append_cell_text(table, EUT_ROWS["rating_power_supply"], 3, overview.rating_power_supply_value)

    set_cell_text(table, EUT_ROWS["tested_condition"], 3, overview.tested_condition)
    set_cell_text(table, EUT_ROWS["date_of_manufacture"], 3, overview.date_of_manufacture)
    set_cell_text(table, EUT_ROWS["manufacturer_name"], 4, overview.manufacturer_name)
    set_cell_text(table, EUT_ROWS["manufacturer_address"], 4, overview.manufacturer_address)
    set_cell_text(table, EUT_ROWS["attachment"], 3, overview.attachment)
    set_cell_text(table, EUT_ROWS["option"], 3, overview.option)
    set_cell_text(table, EUT_ROWS["date_sample_received"], 3, overview.date_sample_received)
    set_cell_text(table, EUT_ROWS["test_engineer"], 3, overview.test_engineer)


def _write_power_supply_checkboxes(doc, overview: EutOverview) -> None:
    types = set(overview.rating_power_supply_types)

    dc_selected = "dc_2p" in types or "dc_2p_e" in types
    single_phase_selected = "single_phase_2p" in types or "single_phase_2p_e" in types
    three_phase_selected = "three_phase_3p_e" in types or "three_phase_4p_e" in types

    set_checkbox(doc, CHECKBOX_INDEX["dc_overall"], dc_selected)
    set_checkbox(doc, CHECKBOX_INDEX["dc_2p"], "dc_2p" in types)
    set_checkbox(doc, CHECKBOX_INDEX["dc_2p_e"], "dc_2p_e" in types)

    set_checkbox(doc, CHECKBOX_INDEX["single_phase_overall"], single_phase_selected)
    set_checkbox(doc, CHECKBOX_INDEX["single_phase_2p"], "single_phase_2p" in types)
    set_checkbox(doc, CHECKBOX_INDEX["single_phase_2p_e"], "single_phase_2p_e" in types)

    set_checkbox(doc, CHECKBOX_INDEX["three_phase_overall"], three_phase_selected)
    set_checkbox(doc, CHECKBOX_INDEX["three_phase_3p_e"], "three_phase_3p_e" in types)
    set_checkbox(doc, CHECKBOX_INDEX["three_phase_4p_e"], "three_phase_4p_e" in types)


def _write_equipment_table(conn, doc, project_id: str) -> None:
    all_equipment = equipment_repository.list_by_project(conn, project_id)
    table = doc.Tables(EQUIPMENT_TABLE)

    offset = 0
    for category, section in EQUIPMENT_SECTIONS.items():
        items = sorted(
            (e for e in all_equipment if e.category == category),
            key=lambda e: (e.sort_order, e.display_id),
        )
        start_row = section["start_row"] + offset
        capacity = section["capacity"]

        extra = ensure_row_capacity(table, start_row, capacity, len(items))
        for i, equipment in enumerate(items):
            row = start_row + i
            _write_equipment_row(table, row, equipment)
        offset += extra


def _write_equipment_row(table, row: int, equipment: Equipment) -> None:
    set_cell_text(table, row, EQUIPMENT_COLUMNS["display_id"], equipment.display_id)
    set_cell_text(table, row, EQUIPMENT_COLUMNS["description"], equipment.description)
    set_cell_text(table, row, EQUIPMENT_COLUMNS["model_name"], equipment.model_name)
    set_cell_text(table, row, EQUIPMENT_COLUMNS["serial"], equipment.serial)
    set_cell_text(table, row, EQUIPMENT_COLUMNS["manufacturer"], equipment.manufacturer)
    fcc_bsmi = equipment.fcc_id or equipment.bsmi_id
    if equipment.fcc_id and equipment.bsmi_id:
        fcc_bsmi = f"{equipment.fcc_id} / {equipment.bsmi_id}"
    set_cell_text(table, row, EQUIPMENT_COLUMNS["fcc_bsmi"], fcc_bsmi)


def _write_cable_table(conn, doc, project_id: str) -> None:
    cables = cable_repository.list_by_project(conn, project_id)
    if not cables:
        return

    table = doc.Tables(CABLE_TABLE)
    ensure_row_capacity(table, CABLE_START_ROW, CABLE_CAPACITY, len(cables))

    for i, cable in enumerate(cables):
        row = CABLE_START_ROW + i
        _write_cable_row(table, row, cable)


def _write_cable_row(table, row: int, cable: Cable) -> None:
    set_cell_text(table, row, CABLE_COLUMNS["cable_no"], str(cable.cable_no))
    set_cell_text(table, row, CABLE_COLUMNS["cable_type"], cable.cable_type)

    length_text = ""
    if cable.length is not None:
        length_text = _fmt_num(cable.length)
        if cable.length_unit != "m":
            length_text += f" {cable.length_unit}"
    set_cell_text(table, row, CABLE_COLUMNS["length"], length_text)

    set_cell_text(table, row, CABLE_COLUMNS["shielded"], SHIELDED_LABELS.get(cable.shielded, ""))
    set_cell_text(table, row, CABLE_COLUMNS["maximum_length"], cable.maximum_length)
    set_cell_text(
        table, row, CABLE_COLUMNS["outdoor_connection"], OUTDOOR_LABELS.get(cable.outdoor_connection, "")
    )


def _write_diagram(doc, diagram_image_path: Path) -> None:
    table = doc.Tables(DIAGRAM_TABLE)
    insert_picture_replacing_cell(table, DIAGRAM_ROW, DIAGRAM_COL, diagram_image_path)


def _fmt_num(value: float | None) -> str:
    if value is None:
        return ""
    if value == int(value):
        return str(int(value))
    return str(value)
