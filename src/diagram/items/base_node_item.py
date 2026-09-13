from __future__ import annotations

from PySide6.QtCore import QRectF, Signal
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject


class NodeItemBase(QGraphicsObject):
    """Equipment/PowerSource/GroundConnectionの構成図Node共通基底クラス。
    子Nodeは Qt の親子Item機能（setParentItem）でContainmentを表現し、
    親を移動すれば子も自動的に追従する（29.節）。"""

    move_finished = Signal(str, float, float, float, float)  # node_id, old_x, old_y, new_x, new_y

    def __init__(self, node_id: str, width: float, height: float) -> None:
        super().__init__()
        self.node_id = node_id
        self._width = width
        self._height = height
        self._press_pos = self.pos()
        self._attached_edges: list = []

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)

    @property
    def width(self) -> float:
        return self._width

    @property
    def height(self) -> float:
        return self._height

    def boundingRect(self) -> QRectF:  # noqa: N802 - Qt overrides
        return QRectF(0, 0, self._width, self._height)

    def set_size(self, width: float, height: float) -> None:
        self.prepareGeometryChange()
        self._width = width
        self._height = height
        self.update()
        for edge in self._attached_edges:
            edge.update_position()

    def attach_edge(self, edge_item) -> None:  # noqa: ANN001 - CableItemとの循環import回避
        self._attached_edges.append(edge_item)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._press_pos = self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        super().mouseReleaseEvent(event)
        if self.pos() != self._press_pos:
            self.move_finished.emit(
                self.node_id, self._press_pos.x(), self._press_pos.y(), self.pos().x(), self.pos().y()
            )

    def itemChange(self, change, value):  # noqa: N802
        if (
            change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
            and isinstance(self.parentItem(), NodeItemBase)
        ):
            parent = self.parentItem()
            max_x = max(parent.width - self._width, 0)
            max_y = max(parent.height - self._height, 0)
            clamped_x = min(max(value.x(), 0), max_x)
            clamped_y = min(max(value.y(), 0), max_y)
            value.setX(clamped_x)
            value.setY(clamped_y)
            return value

        if change in (
            QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged,
            QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged,
        ):
            for edge in self._attached_edges:
                edge.update_position()

        return super().itemChange(change, value)
