from __future__ import annotations

from PySide6.QtCore import QLineF, Qt
from PySide6.QtGui import QPen

from diagram.items.base_node_item import NodeItemBase


class GroundItem(NodeItemBase):
    """GND/Earthを一般的な接地記号（3本の水平線が下に向かって短くなる形）で表示する（23.節）。"""

    def __init__(self, node_id: str, width: float, height: float) -> None:
        super().__init__(node_id, width, height)

    def paint(self, painter, option, widget=None) -> None:  # noqa: N802
        painter.setPen(QPen(Qt.GlobalColor.black, 2 if self.isSelected() else 1))

        center_x = self._width / 2
        top_y = 0.0
        painter.drawLine(QLineF(center_x, top_y, center_x, self._height * 0.4))

        line_widths = [self._width * 0.8, self._width * 0.5, self._width * 0.25]
        for i, line_width in enumerate(line_widths):
            y = self._height * 0.4 + i * (self._height * 0.2)
            painter.drawLine(QLineF(center_x - line_width / 2, y, center_x + line_width / 2, y))
