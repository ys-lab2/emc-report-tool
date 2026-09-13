from __future__ import annotations

import sqlite3

from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoCommand

from diagram.items.cable_item import CableItem
from services import diagram_service


class UpdateRouteCommand(QUndoCommand):
    """ケーブル線の中間点（折れ線ルート）追加・削除・移動をUndo/Redo対象にする。"""

    def __init__(
        self,
        conn: sqlite3.Connection,
        edge_id: str,
        item: CableItem,
        old_points: list[QPointF],
        new_points: list[QPointF],
    ) -> None:
        super().__init__("ケーブル経路変更")
        self._conn = conn
        self._edge_id = edge_id
        self._item = item
        self._old_points = list(old_points)
        self._new_points = list(new_points)

    def redo(self) -> None:
        self._item.set_route_points(self._new_points)
        diagram_service.update_edge_route(self._conn, self._edge_id, _to_tuples(self._new_points))

    def undo(self) -> None:
        self._item.set_route_points(self._old_points)
        diagram_service.update_edge_route(self._conn, self._edge_id, _to_tuples(self._old_points))


def _to_tuples(points: list[QPointF]) -> list[tuple[float, float]]:
    return [(p.x(), p.y()) for p in points]
