from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QPen
from PySide6.QtWidgets import QApplication

from diagram.items.base_node_item import NodeItemBase


class PowerSourceItem(NodeItemBase):
    """電源はEquipmentとは別のNodeとして丸形で表示する（22.節）。"""

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

    def default_fill_color(self):
        from PySide6.QtGui import QColor

        return QColor("#fdf3d8")

    def paint(self, painter, option, widget=None) -> None:  # noqa: N802
        rect = self.boundingRect()
        painter.setPen(QPen(self.effective_stroke_color(), 2 if self.isSelected() else 1))
        painter.setBrush(QBrush(self.effective_fill_color()))
        painter.drawEllipse(rect)

        app = QApplication.instance()
        if app is not None:
            painter.setFont(app.font())
        painter.setPen(QPen(self.effective_stroke_color()))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "\n".join(self.label_lines))
