"""ユーザーフィードバックを受けて追加した機能の統合テスト（Word COM必須）。
F)寸法表の再構築、G)周波数表の再構築、O)動作モード、申請者情報、プロジェクト備考を検証する。
"""

import pytest
import win32com.client

from models.applicant import Applicant
from models.equipment import Equipment
from models.eut_overview import EutOverview, Frequency
from models.operation_mode import OperationMode
from repositories import applicant_repository, eut_overview_repository, operation_mode_repository
from services import equipment_service, export_service, project_service


def _word_available() -> bool:
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Quit()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _word_available(), reason="Microsoft Word is not available")


def _read_cell(doc, table_index: int, row: int, col: int) -> str:
    text = doc.Tables(table_index).Cell(row, col).Range.Text
    return text.replace("\r", "").replace("\x07", "").strip()


@pytest.fixture
def populated_handle(tmp_path):
    handle = project_service.create_new(tmp_path / "PJ_V2FIX.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    handle.project.notes = "特記事項：追加のシールド対策が必要。"
    project_service.save(handle)

    applicant_repository.upsert(
        conn,
        Applicant(
            applicant_id="",
            project_id=project_id,
            company_name_jp="サンプル株式会社",
            address_jp="東京都渋谷区1-2-3",
            company_name_en="Sample Co., Ltd.",
            address_en="1-2-3, Shibuya, Tokyo",
        ),
    )

    overview = eut_overview_repository.upsert(
        conn, EutOverview(eut_overview_id="", project_id=project_id, max_frequency="230MHz")
    )
    eut_overview_repository.add_frequency(
        conn, Frequency(frequency_id="", eut_overview_id=overview.eut_overview_id, value="18MHz", usage_note="CPU")
    )
    eut_overview_repository.add_frequency(
        conn, Frequency(frequency_id="", eut_overview_id=overview.eut_overview_id, value="230MHz", usage_note="発信周波数")
    )

    operation_mode_repository.add(
        conn,
        OperationMode(
            operation_mode_id="", project_id=project_id, mode_name="通常動作モード", description="電源投入後、自動計測を行う。"
        ),
    )

    equipment_service.create_equipment(
        conn,
        Equipment(
            equipment_id="", project_id=project_id, display_id="A", category="EUT",
            description="EUT本体", width_mm=230, depth_mm=230, height_mm=230,
        ),
    )
    equipment_service.create_equipment(
        conn,
        Equipment(
            equipment_id="", project_id=project_id, display_id="B", category="EUT",
            description="EUTサブユニット", width_mm=500, depth_mm=600, height_mm=730,
        ),
    )

    yield handle
    handle.close()


def test_dimension_table_has_one_row_per_eut(populated_handle, tmp_path):
    output_path = tmp_path / "output_v2.docx"
    export_service.export_to_word(populated_handle, output_path, render_diagram=False)

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(output_path), ReadOnly=True)
        try:
            outer_table = doc.Tables(4)
            dimension_cell = outer_table.Cell(9, 3)
            nested = dimension_cell.Tables(1)

            assert nested.Rows.Count == 3  # header + EUT1 + EUT2
            assert _cell_text(nested, 1, 2) == "Width"
            assert _cell_text(nested, 2, 1) == "EUT1"
            assert _cell_text(nested, 2, 2) == "230"
            assert _cell_text(nested, 3, 1) == "EUT2"
            assert _cell_text(nested, 3, 3) == "600"
        finally:
            doc.Close(False)
    finally:
        word.Quit()


def test_frequency_table_lists_all_entries(populated_handle, tmp_path):
    output_path = tmp_path / "output_v2b.docx"
    export_service.export_to_word(populated_handle, output_path, render_diagram=False)

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(output_path), ReadOnly=True)
        try:
            outer_table = doc.Tables(4)
            freq_cell = outer_table.Cell(10, 3)
            nested = freq_cell.Tables(1)

            assert nested.Rows.Count == 4  # header + max + 2 list entries
            assert _cell_text(nested, 2, 1) == "230MHz"
            assert _cell_text(nested, 3, 1) == "18MHz"
            assert _cell_text(nested, 3, 2) == "CPU"
            assert _cell_text(nested, 4, 1) == "230MHz"
        finally:
            doc.Close(False)
    finally:
        word.Quit()


def test_operation_mode_and_applicant_and_notes_exported(populated_handle, tmp_path):
    output_path = tmp_path / "output_v2c.docx"
    export_service.export_to_word(populated_handle, output_path, render_diagram=False)

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(output_path), ReadOnly=True)
        try:
            assert _read_cell(doc, 4, 20, 4) == "通常動作モード"
            assert "電源投入後" in _read_cell(doc, 4, 21, 4)

            assert _read_cell(doc, 3, 11, 3) == "サンプル株式会社"
            assert _read_cell(doc, 3, 12, 3) == "東京都渋谷区1-2-3"
            assert _read_cell(doc, 3, 13, 3) == "Sample Co., Ltd."
            assert _read_cell(doc, 3, 14, 3) == "1-2-3, Shibuya, Tokyo"

            note_text = _read_cell(doc, 2, 1, 2)
            assert "特記事項" in note_text
        finally:
            doc.Close(False)
    finally:
        word.Quit()


def _cell_text(table, row: int, col: int) -> str:
    return table.Cell(row, col).Range.Text.replace("\r", "").replace("\x07", "").strip()
