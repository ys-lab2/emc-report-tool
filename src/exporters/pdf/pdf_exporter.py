"""Word→PDF変換。独自PDF帳票エンジンは作らず、Microsoft Wordの
ExportAsFixedFormatを使うことでWordとPDFの見た目を一致させる（50.節）。"""

from __future__ import annotations

from pathlib import Path

from exporters.word.base import word_application

WD_EXPORT_FORMAT_PDF = 17  # Word定数 wdExportFormatPDF


def convert_docx_to_pdf(docx_path: Path, pdf_path: Path) -> Path:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    with word_application(visible=False) as word:
        doc = word.Documents.Open(str(docx_path))
        try:
            doc.ExportAsFixedFormat(OutputFileName=str(pdf_path), ExportFormat=WD_EXPORT_FORMAT_PDF)
        finally:
            doc.Close(False)

    return pdf_path
