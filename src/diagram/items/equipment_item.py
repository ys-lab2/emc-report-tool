from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import QApplication

from diagram.items.base_node_item import NodeItemBase

HANDLE_SIZE = 10.0
MIN_WIDTH = 60.0
MIN_HEIGHT = 40.0


class EquipmentItem(NodeItemBase):
    resize_finished = Signal(str, float, float, float, float)  # node_id, old_w, old_h, new_w, new_h

    def __init__(
        self,
        node_id: str,
        width: float,
        height: float,
        label_lines: list[str],
        fill_color: str | None = None,
        stroke_color: str | None = None,
    ) -> None:
        super().__init__(node_id, width, height, fill_color, stroke_color)
        self.label_lines = label_lines
        self._resizing = False
        self._resize_start_size = (width, height)
        self._resize_start_mouse = None

    def _handle_rect(self) -> QRectF:
        return QRectF(self._width - HANDLE_SIZE, self._height - HANDLE_SIZE, HANDLE_SIZE, HANDLE_SIZE)

    def paint(self, painter, option, widget=None) -> None:  # noqa: N802
        rect = self.boundingRect()
        pen = QPen(self.effective_stroke_color(), 2 if self.isSelected() else 1)
        if not self.clamp_to_parent and self.parentItem() is not None:
            # 外付け取付（attached）は内蔵と区別するため破線枠にする（14.節）
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.effective_fill_color()))
        painter.drawRect(rect)

        app = QApplication.instance()
        if app is not None:
            painter.setFont(app.font())
        painter.setPen(QPen(self.effective_stroke_color()))
        for i, line in enumerate(self.label_lines):
            painter.drawText(
                QRectF(4, 4 + i * 16, self._width - 8, 16),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                line,
            )

        if self.isSelected():
            painter.setBrush(QBrush(QColor("#7a7a7a")))
            painter.setPen(QPen(Qt.GlobalColor.darkGray))
            painter.drawRect(self._handle_rect())

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self._handle_rect().contains(event.pos()):
            self._resizing = True
            self._resize_start_size = (self._width, self._height)
            self._resize_start_mouse = event.scenePos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._resizing:
            delta = event.scenePos() - self._resize_start_mouse
            new_width = max(MIN_WIDTH, self._resize_start_size[0] + delta.x())
            new_height = max(MIN_HEIGHT, self._resize_start_size[1] + delta.y())
            self.set_size(new_width, new_height)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._resizing:
            self._resizing = False
            old_w, old_h = self._resize_start_size
            if (old_w, old_h) != (self._width, self._height):
                self.resize_finished.emit(self.node_id, old_w, old_h, self._width, self._height)
            event.accept()
            return
        super().mouseReleaseEvent(event)
