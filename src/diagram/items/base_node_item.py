from __future__ import annotations

from PySide6.QtCore import QRectF, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QGraphicsItem, QGraphicsObject, QMenu


class NodeItemBase(QGraphicsObject):
    """Equipment/PowerSource/GroundConnectionの構成図Node共通基底クラス。
    子Nodeは Qt の親子Item機能（setParentItem）でContainmentを表現し、
    親を移動すれば子も自動的に追従する（29.節）。"""

    move_finished = Signal(str, float, float, float, float)  # node_id, old_x, old_y, new_x, new_y
    colors_changed = Signal(str, object, object, object, object)  # node_id, old_fill, old_stroke, new_fill, new_stroke

    SUPPORTS_FILL = True

    def __init__(
        self,
        node_id: str,
        width: float,
        height: float,
        fill_color: str | None = None,
        stroke_color: str | None = None,
    ) -> None:
        super().__init__()
        self.node_id = node_id
        self._width = width
        self._height = height
        self._press_pos = self.pos()
        self._attached_edges: list = []
        self.fill_color: str | None = fill_color
        self.stroke_color: str | None = stroke_color
        # 外付け取付（attached）のEquipmentは親の枠内に収めず、側面にはみ出せるようにする
        # （14.節・25.節：内蔵/挿入とは見た目を区別する）。既定は内蔵と同じ「枠内に収める」。
        self.clamp_to_parent: bool = True

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

    def default_fill_color(self) -> QColor:
        return QColor("#eaf1fb")

    def default_stroke_color(self) -> QColor:
        return QColor(0, 0, 0)  # black

    def effective_fill_color(self) -> QColor:
        return QColor(self.fill_color) if self.fill_color else self.default_fill_color()

    def effective_stroke_color(self) -> QColor:
        return QColor(self.stroke_color) if self.stroke_color else self.default_stroke_color()

    def boundingRect(self) -> QRectF:  # noqa: N802 - Qt overrides
        return QRectF(0, 0, self._width, self._height)

    def set_size(self, width: float, height: float) -> None:
        self.prepareGeometryChange()
        self._width = width
        self._height = height
        self.update()
        for edge in self._attached_edges:
            edge.update_position()

    def set_colors(self, fill_color: str | None, stroke_color: str | None) -> None:
        self.fill_color = fill_color
        self.stroke_color = stroke_color
        self.update()

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

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = QMenu()
        stroke_action = menu.addAction("線の色を変更...")
        fill_action = menu.addAction("塗りつぶし色を変更...") if self.SUPPORTS_FILL else None
        reset_action = menu.addAction("色をリセット")

        chosen = menu.exec(event.screenPos())
        if chosen is None:
            return

        old_fill, old_stroke = self.fill_color, self.stroke_color

        if chosen is stroke_action:
            color = QColorDialog.getColor(self.effective_stroke_color(), None, "線の色を選択")
            if not color.isValid():
                return
            new_stroke = color.name()
            new_fill = self.fill_color
        elif fill_action is not None and chosen is fill_action:
            color = QColorDialog.getColor(self.effective_fill_color(), None, "塗りつぶし色を選択")
            if not color.isValid():
                return
            new_fill = color.name()
            new_stroke = self.stroke_color
        elif chosen is reset_action:
            new_fill, new_stroke = None, None
        else:
            return

        self.set_colors(new_fill, new_stroke)
        self.colors_changed.emit(self.node_id, old_fill, old_stroke, new_fill, new_stroke)

    def itemChange(self, change, value):  # noqa: N802
        if (
            change == QGraphicsItem.GraphicsItemChange.ItemPositionChange
            and isinstance(self.parentItem(), NodeItemBase)
            and self.clamp_to_parent
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
