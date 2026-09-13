from __future__ import annotations

from PySide6.QtCore import QLineF, QRectF, Qt
from PySide6.QtGui import QPen
from PySide6.QtWidgets import QApplication

from diagram.items.base_node_item import NodeItemBase


class GroundItem(NodeItemBase):
    """GND/Earthを一般的な接地記号（3本の水平線が下に向かって短くなる形）で表示する（23.節）。
    塗りつぶしの概念が無いため、色カスタマイズは線色のみ対応する。"""

    SUPPORTS_FILL = False

    def __init__(
        self,
        node_id: str,
        width: float,
        height: float,
        label_lines: list[str] | None = None,
        fill_color: str | None = None,
        stroke_color: str | None = None,
    ) -> None:
        super().__init__(node_id, width, height, fill_color, stroke_color)
        self.label_lines = label_lines or []

    def boundingRect(self) -> QRectF:  # noqa: N802
        base = QRectF(0, 0, self._width, self._height)
        if self.label_lines:
            return base.adjusted(-20, 0, 20, 20)
        return base

    def paint(self, painter, option, widget=None) -> None:  # noqa: N802
        pen = QPen(self.effective_stroke_color(), 2 if self.isSelected() else 1)
        painter.setPen(pen)

        center_x = self._width / 2
        top_y = 0.0
        painter.drawLine(QLineF(center_x, top_y, center_x, self._height * 0.4))

        line_widths = [self._width * 0.8, self._width * 0.5, self._width * 0.25]
        for i, line_width in enumerate(line_widths):
            y = self._height * 0.4 + i * (self._height * 0.2)
            painter.drawLine(QLineF(center_x - line_width / 2, y, center_x + line_width / 2, y))

        if self.label_lines:
            app = QApplication.instance()
            if app is not None:
                painter.setFont(app.font())
            painter.drawText(
                QRectF(-20, self._height + 2, self._width + 40, 16),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                " ".join(self.label_lines),
            )
