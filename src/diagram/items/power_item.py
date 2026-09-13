from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen

from diagram.items.base_node_item import NodeItemBase


class PowerSourceItem(NodeItemBase):
    """電源はEquipmentとは別のNodeとして丸形で表示する（22.節）。"""

    def __init__(self, node_id: str, width: float, height: float, label_lines: list[str]) -> None:
        super().__init__(node_id, width, height)
        self.label_lines = label_lines

    def paint(self, painter, option, widget=None) -> None:  # noqa: N802
        rect = self.boundingRect()
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if self.isSelected() else 1))
        painter.setBrush(QBrush(QColor("#fdf3d8")))
        painter.drawEllipse(rect)

        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "\n".join(self.label_lines))
