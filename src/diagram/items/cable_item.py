from __future__ import annotations

import math

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsObject, QMenu

from diagram.items.base_node_item import NodeItemBase

LABEL_MARGIN = 60.0
POINT_HIT_RADIUS = 9.0
SEGMENT_HIT_DISTANCE = 7.0
POINT_HANDLE_SIZE = 7.0


class CableItem(QGraphicsObject):
    """Cableの構成図上の線表現。直線、または中間点を挟んだ複数の直線区間（折れ線）で
    From/ToのNodeを結ぶ（30.節）。他図形と重ならないよう鋭角に迂回させたい場合を想定し、
    曲線（ベジェ曲線等）は採用しない。中間点は右クリックで追加・削除、ドラッグで移動できる。"""

    route_changed = Signal(str, object, object)  # edge_id, old_points(list[QPointF]), new_points(list[QPointF])

    def __init__(
        self,
        edge_id: str,
        from_item: NodeItemBase,
        to_item: NodeItemBase,
        label_lines: list[str],
        route_points: list[QPointF] | None = None,
    ) -> None:
        super().__init__()
        self.edge_id = edge_id
        self.from_item = from_item
        self.to_item = to_item
        self.label_lines = label_lines
        self.route_points: list[QPointF] = list(route_points) if route_points else []
        self.setZValue(-1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)

        self._dragging_index: int | None = None
        self._drag_start_route: list[QPointF] = []

        from_item.attach_edge(self)
        to_item.attach_edge(self)

    def _anchor(self, item: NodeItemBase) -> QPointF:
        return item.mapToScene(item.boundingRect().center())

    def full_path(self) -> list[QPointF]:
        return [self._anchor(self.from_item), *self.route_points, self._anchor(self.to_item)]

    def boundingRect(self) -> QRectF:  # noqa: N802
        path = self.full_path()
        xs = [p.x() for p in path]
        ys = [p.y() for p in path]
        rect = QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
        return rect.adjusted(-LABEL_MARGIN, -LABEL_MARGIN, LABEL_MARGIN, LABEL_MARGIN)

    def paint(self, painter, option, widget=None) -> None:  # noqa: N802
        path = self.full_path()

        pen = QPen(Qt.GlobalColor.yellow if self.isSelected() else Qt.GlobalColor.darkGray, 2)
        painter.setPen(pen)
        for i in range(len(path) - 1):
            painter.drawLine(QLineF(path[i], path[i + 1]))

        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.darkGray))
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            for point in self.route_points:
                painter.drawRect(
                    QRectF(
                        point.x() - POINT_HANDLE_SIZE / 2,
                        point.y() - POINT_HANDLE_SIZE / 2,
                        POINT_HANDLE_SIZE,
                        POINT_HANDLE_SIZE,
                    )
                )

        mid = self._label_anchor(path)
        painter.setPen(QPen(Qt.GlobalColor.black))
        for i, line in enumerate(self.label_lines):
            painter.drawText(mid + QPointF(4, i * 14 - 4), line)

    def _label_anchor(self, path: list[QPointF]) -> QPointF:
        first_mid_index = 0
        p1, p2 = path[first_mid_index], path[first_mid_index + 1]
        return QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)

    def update_position(self) -> None:
        self.prepareGeometryChange()
        self.update()

    def set_route_points(self, points: list[QPointF]) -> None:
        self.prepareGeometryChange()
        self.route_points = list(points)
        self.update()

    # --- 中間点の追加・削除・ドラッグ操作 ---

    def _point_index_at(self, scene_pos: QPointF) -> int | None:
        for i, point in enumerate(self.route_points):
            if (point - scene_pos).manhattanLength() <= POINT_HIT_RADIUS * 2:
                if math.hypot(point.x() - scene_pos.x(), point.y() - scene_pos.y()) <= POINT_HIT_RADIUS:
                    return i
        return None

    def _segment_insert_index_at(self, scene_pos: QPointF) -> int | None:
        path = self.full_path()
        best_index = None
        best_distance = SEGMENT_HIT_DISTANCE
        for i in range(len(path) - 1):
            distance = _distance_to_segment(scene_pos, path[i], path[i + 1])
            if distance <= best_distance:
                best_distance = distance
                best_index = i
        return best_index

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            index = self._point_index_at(event.scenePos())
            if index is not None:
                self.setSelected(True)
                self._dragging_index = index
                self._drag_start_route = list(self.route_points)
                event.accept()
                return
            self.setSelected(True)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._dragging_index is not None:
            self.prepareGeometryChange()
            self.route_points[self._dragging_index] = event.scenePos()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if self._dragging_index is not None:
            old_route = self._drag_start_route
            new_route = list(self.route_points)
            self._dragging_index = None
            self._drag_start_route = []
            if [(p.x(), p.y()) for p in old_route] != [(p.x(), p.y()) for p in new_route]:
                self.route_changed.emit(self.edge_id, old_route, new_route)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        scene_pos = event.scenePos()
        point_index = self._point_index_at(scene_pos)

        menu = QMenu()
        if point_index is not None:
            remove_action = menu.addAction("この中間点を削除")
        else:
            insert_index = self._segment_insert_index_at(scene_pos)
            add_action = menu.addAction("ここに中間点を追加（折れ線にする）") if insert_index is not None else None

        chosen = menu.exec(event.screenPos())

        if point_index is not None and chosen is remove_action:
            old_route = list(self.route_points)
            new_route = list(self.route_points)
            del new_route[point_index]
            self.set_route_points(new_route)
            self.route_changed.emit(self.edge_id, old_route, new_route)
        elif point_index is None:
            insert_index = self._segment_insert_index_at(scene_pos)
            if insert_index is not None and chosen is add_action:
                old_route = list(self.route_points)
                new_route = list(self.route_points)
                new_route.insert(insert_index, scene_pos)
                self.set_route_points(new_route)
                self.route_changed.emit(self.edge_id, old_route, new_route)


def _distance_to_segment(point: QPointF, seg_start: QPointF, seg_end: QPointF) -> float:
    seg_vec = seg_end - seg_start
    seg_len_sq = seg_vec.x() ** 2 + seg_vec.y() ** 2
    if seg_len_sq == 0:
        return math.hypot(point.x() - seg_start.x(), point.y() - seg_start.y())

    t = ((point.x() - seg_start.x()) * seg_vec.x() + (point.y() - seg_start.y()) * seg_vec.y()) / seg_len_sq
    t = max(0.0, min(1.0, t))
    closest = QPointF(seg_start.x() + t * seg_vec.x(), seg_start.y() + t * seg_vec.y())
    return math.hypot(point.x() - closest.x(), point.y() - closest.y())
