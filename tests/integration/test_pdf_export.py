"""Word→PDF変換の統合テスト（Word COM必須）。"""

import fitz  # PyMuPDF
import pytest
import win32com.client

from models.equipment import Equipment
from services import equipment_service, export_service, project_service


def _word_available() -> bool:
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Quit()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _word_available(), reason="Microsoft Word is not available")


def test_export_to_pdf_produces_readable_pdf(tmp_path):
    handle = project_service.create_new(tmp_path / "PJ_PDF_TEST.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    handle.project.project_no = "PJ260123"
    project_service.save(handle)

    equipment_service.create_equipment(
        conn,
        Equipment(equipment_id="", project_id=project_id, display_id="A", category="EUT", description="EUT本体"),
    )

    output_path = tmp_path / "report.pdf"
    export_service.export_to_pdf(handle, output_path, render_diagram=False)

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    pdf = fitz.open(str(output_path))
    try:
        assert pdf.page_count >= 5  # word-template-analysis.md 実測: 9ページ構成
        first_page_text = pdf[0].get_text()
        assert "PJ260123" in first_page_text
    finally:
        pdf.close()

    handle.close()
