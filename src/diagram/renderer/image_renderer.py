from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter

from diagram.scene import DiagramScene

MARGIN = 20.0
DEFAULT_SCALE = 2.0  # Word/PDF埋め込み用に高解像度化する（49.節）


def render_scene_to_png(scene: DiagramScene, output_path: Path, scale: float = DEFAULT_SCALE) -> Path:
    """構成図をPNG画像として書き出す。Word/PDF/Excelで同じ画像を再利用する（49.節・51.節）。
    Qtの制約上SVGではなくPNGを第一実装とする（アーキテクチャ設計で許容されたフォールバック）。"""
    rect = scene.itemsBoundingRect()
    if rect.isEmpty():
        rect = QRectF(0, 0, 400, 300)
    rect = rect.adjusted(-MARGIN, -MARGIN, MARGIN, MARGIN)

    width = max(int(rect.width() * scale), 1)
    height = max(int(rect.height() * scale), 1)

    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.white)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    scene.render(painter, QRectF(0, 0, width, height), rect)
    painter.end()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(output_path))
    return output_path
