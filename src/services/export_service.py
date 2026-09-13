from __future__ import annotations

import tempfile
from pathlib import Path

from diagram.renderer.image_renderer import render_scene_to_png
from diagram.scene import DiagramScene
from exporters.pdf.pdf_exporter import convert_docx_to_pdf
from exporters.word import fm05_v36
from exporters.word.registry import resolve_exporter
from services.project_service import ProjectHandle
from utils.app_paths import app_base_dir

TEMPLATE_DIR = app_base_dir() / "テンプレート"
DEFAULT_TEMPLATE_FILENAME = "MM-QR-001_FM05_テストレポート作成資料_Ver.3-6 (2025.03.25).docx"
DEFAULT_TEMPLATE_PATH = TEMPLATE_DIR / DEFAULT_TEMPLATE_FILENAME


def export_to_word(
    handle: ProjectHandle,
    output_path: Path,
    template_path: Path | None = None,
    render_diagram: bool = True,
) -> Path:
    """現在のプロジェクトをWordテンプレートへ出力する（Phase 3のMVP中核機能）。
    出力先セルの根拠は docs/word-template-analysis.md 9A.節を参照。"""
    template_path = template_path or DEFAULT_TEMPLATE_PATH
    if not template_path.exists():
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_path}")

    exporter = resolve_exporter(fm05_v36.TEMPLATE_ID, fm05_v36.TEMPLATE_VERSION)

    diagram_image_path = None
    if render_diagram:
        diagram_image_path = _render_diagram_image(handle)

    return exporter.export(handle, template_path, output_path, diagram_image_path)


def export_to_pdf(
    handle: ProjectHandle,
    output_path: Path,
    template_path: Path | None = None,
    render_diagram: bool = True,
) -> Path:
    """Word生成 → Microsoft Word → ExportAsFixedFormat という順で変換する（50.節）。
    独自PDFレンダリングは行わず、Word出力と見た目を一致させる。"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_docx_path = Path(tmp_dir) / f"{handle.file_path.stem}.docx"
        export_to_word(handle, temp_docx_path, template_path=template_path, render_diagram=render_diagram)
        convert_docx_to_pdf(temp_docx_path, output_path)

    return output_path


def _render_diagram_image(handle: ProjectHandle) -> Path | None:
    from PySide6.QtGui import QUndoStack

    scene = DiagramScene(QUndoStack())
    scene.set_project(handle.connection, handle.project.project_id)
    if not scene.items():
        return None

    temp_path = Path(tempfile.gettempdir()) / f"emc_diagram_{handle.project.project_id}.png"
    return render_scene_to_png(scene, temp_path)
