"""構成図画像を含むWord出力の統合テスト（Word COM必須）。"""

import pytest
import win32com.client

from models.cable import Cable
from models.equipment import Equipment
from services import cable_service, equipment_service, export_service, project_service


def _word_available() -> bool:
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Quit()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _word_available(), reason="Microsoft Word is not available")


def test_export_inserts_rendered_diagram_image(tmp_path):
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])

    handle = project_service.create_new(tmp_path / "PJ_DIAGRAM_EXPORT.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    a = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project_id, display_id="A", category="EUT", description="EUT")
    )
    b = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project_id, display_id="B", category="Peripheral", description="PC")
    )
    cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project_id, from_equipment_id=a.equipment_id, to_equipment_id=b.equipment_id, cable_type="USB")
    )

    output_path = tmp_path / "output_diagram.docx"
    export_service.export_to_word(handle, output_path, render_diagram=True)

    assert output_path.exists()

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(str(output_path), ReadOnly=True)
        try:
            table = doc.Tables(7)
            cell = table.Cell(2, 1)
            assert cell.Range.InlineShapes.Count >= 1
        finally:
            doc.Close(False)
    finally:
        word.Quit()

    handle.close()
