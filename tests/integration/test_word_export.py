"""Word COMを実際に使う統合テスト。Microsoft Wordがインストールされた環境でのみ実行可能。
docs/architecture.md 9.節の方針により、Word COM依存のテストはここに隔離する。"""

import pytest
import win32com.client

from models.cable import Cable
from models.equipment import Equipment
from models.eut_overview import EutOverview
from models.report_standard import ReportStandard
from repositories import eut_overview_repository, report_standard_repository
from services import cable_service, equipment_service, export_service, project_service


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
    handle = project_service.create_new(tmp_path / "PJ_EXPORT_TEST.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    handle.project.project_no = "PJ260099"
    handle.project.test_plan_no = "TP-099"
    handle.project.measurement_period = "2026/01/10-2026/01/12"
    project_service.save(handle)

    report_standard_repository.add(
        conn,
        ReportStandard(
            report_standard_id="",
            project_id=project_id,
            standard_name="CISPR 32",
            language="jp",
            desired_due_date="2026/02/01",
            submission_media="PDF",
        ),
    )

    eut_overview_repository.upsert(
        conn,
        EutOverview(
            eut_overview_id="",
            project_id=project_id,
            kind_of_equipment="ネットワーク機器",
            model_name="ABC-100",
            serial_no="SN00123",
            sample_type="mass_production",
            width_mm=100,
            depth_mm=50,
            height_mm=30,
            rating_power_supply_types=["dc_2p_e"],
            rating_power_supply_value="DC 24V, 2A",
            manufacturer_name="テスト製造株式会社",
            test_engineer="山田太郎",
        ),
    )

    eut = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project_id, display_id="A", category="EUT", description="EUT本体", model_name="ABC-100")
    )
    peripheral = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project_id, display_id="D", category="Peripheral", description="PC", model_name="Latitude")
    )
    cable_service.create_cable(
        conn,
        Cable(cable_id="", project_id=project_id, from_equipment_id=eut.equipment_id, to_equipment_id=peripheral.equipment_id, cable_type="USB", length=1.5, shielded="shielded"),
    )

    yield handle
    handle.close()


def test_export_writes_project_info_and_eut_overview(populated_handle, tmp_path):
    output_path = tmp_path / "output.docx"

    export_service.export_to_word(populated_handle, output_path, render_diagram=False)

    assert output_path.exists()

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(output_path), ReadOnly=True)
        try:
            assert _read_cell(doc, 1, 1, 2) == "PJ260099"
            assert _read_cell(doc, 1, 2, 2) == "TP-099"

            assert _read_cell(doc, 3, 3, 3) == "CISPR 32"
            assert _read_cell(doc, 3, 3, 4) == "和文"

            assert _read_cell(doc, 4, 2, 3) == "ネットワーク機器"
            assert _read_cell(doc, 4, 3, 3) == "ABC-100"
            assert _read_cell(doc, 4, 5, 3) == "SN00123"

            mass_production_checked = doc.ContentControls(1).Checked
            assert mass_production_checked is True

            dc_overall_checked = doc.ContentControls(3).Checked
            dc_2p_e_checked = doc.ContentControls(5).Checked
            assert dc_overall_checked is True
            assert dc_2p_e_checked is True

            assert _read_cell(doc, 5, 4, 1) == "A"
            assert _read_cell(doc, 5, 4, 2) == "EUT本体"
            assert _read_cell(doc, 5, 8, 1) == "D"
            assert _read_cell(doc, 5, 8, 2) == "PC"

            assert _read_cell(doc, 6, 4, 2) == "USB"
            assert _read_cell(doc, 6, 4, 4) == "Shielded"
        finally:
            doc.Close(False)
    finally:
        word.Quit()


def test_export_duplicates_rows_when_exceeding_capacity(tmp_path):
    handle = project_service.create_new(tmp_path / "PJ_EXPORT_OVERFLOW.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    eut_items = []
    for i in range(5):  # テンプレート固定枠は3行、5件で2行超過させる
        eq = equipment_service.create_equipment(
            conn,
            Equipment(equipment_id="", project_id=project_id, display_id=chr(ord("A") + i), category="EUT", description=f"EUT-{i}"),
        )
        eut_items.append(eq)

    output_path = tmp_path / "output_overflow.docx"
    export_service.export_to_word(handle, output_path, render_diagram=False)

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(output_path), ReadOnly=True)
        try:
            table = doc.Tables(5)
            # EUT行が5行に拡張され、それぞれの内容が正しいこと
            for i in range(5):
                row = 4 + i
                assert _read_cell(doc, 5, row, 1) == chr(ord("A") + i)
                assert _read_cell(doc, 5, row, 2) == f"EUT-{i}"
            # 拡張後もPeripheral見出し行が存在する（行がずれて壊れていないこと）
            assert "Peripherals" in _read_cell(doc, 5, 9, 1) or "周辺機器" in _read_cell(doc, 5, 9, 1)
        finally:
            doc.Close(False)
    finally:
        word.Quit()

    handle.close()
