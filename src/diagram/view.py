from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView

ZOOM_STEP = 1.15
MIN_SCALE = 0.2
MAX_SCALE = 5.0


class DiagramView(QGraphicsView):
    def __init__(self) -> None:
        super().__init__()
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self._scale_factor = 1.0

    def wheelEvent(self, event) -> None:  # noqa: N802
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def zoom_in(self) -> None:
        self._apply_zoom(ZOOM_STEP)

    def zoom_out(self) -> None:
        self._apply_zoom(1 / ZOOM_STEP)

    def _apply_zoom(self, factor: float) -> None:
        new_scale = self._scale_factor * factor
        if new_scale < MIN_SCALE or new_scale > MAX_SCALE:
            return
        self._scale_factor = new_scale
        self.scale(factor, factor)

    def reset_zoom(self) -> None:
        self.resetTransform()
        self._scale_factor = 1.0

    def fit_to_view(self) -> None:
        if self.scene() is None:
            return
        rect = self.scene().itemsBoundingRect()
        if rect.isEmpty():
            return
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self._scale_factor = self.transform().m11()
