from __future__ import annotations

import sqlite3

from PySide6.QtGui import QUndoCommand

from diagram.items.base_node_item import NodeItemBase
from diagram.items.equipment_item import EquipmentItem
from services import diagram_service


class MoveNodeCommand(QUndoCommand):
    def __init__(
        self,
        conn: sqlite3.Connection,
        node_id: str,
        item: NodeItemBase,
        old_pos: tuple[float, float],
        new_pos: tuple[float, float],
    ) -> None:
        super().__init__("Node移動")
        self._conn = conn
        self._node_id = node_id
        self._item = item
        self._old_pos = old_pos
        self._new_pos = new_pos

    def redo(self) -> None:
        self._item.setPos(*self._new_pos)
        diagram_service.move_node(self._conn, self._node_id, *self._new_pos)

    def undo(self) -> None:
        self._item.setPos(*self._old_pos)
        diagram_service.move_node(self._conn, self._node_id, *self._old_pos)


class ChangeNodeColorCommand(QUndoCommand):
    def __init__(
        self,
        conn: sqlite3.Connection,
        node_id: str,
        item: NodeItemBase,
        old_colors: tuple[str | None, str | None],
        new_colors: tuple[str | None, str | None],
    ) -> None:
        super().__init__("Node色変更")
        self._conn = conn
        self._node_id = node_id
        self._item = item
        self._old_colors = old_colors
        self._new_colors = new_colors

    def redo(self) -> None:
        self._item.set_colors(*self._new_colors)
        diagram_service.set_node_colors(self._conn, self._node_id, *self._new_colors)

    def undo(self) -> None:
        self._item.set_colors(*self._old_colors)
        diagram_service.set_node_colors(self._conn, self._node_id, *self._old_colors)


class ResizeNodeCommand(QUndoCommand):
    def __init__(
        self,
        conn: sqlite3.Connection,
        node_id: str,
        item: EquipmentItem,
        old_size: tuple[float, float],
        new_size: tuple[float, float],
    ) -> None:
        super().__init__("Nodeサイズ変更")
        self._conn = conn
        self._node_id = node_id
        self._item = item
        self._old_size = old_size
        self._new_size = new_size

    def redo(self) -> None:
        self._item.set_size(*self._new_size)
        diagram_service.resize_node(self._conn, self._node_id, *self._new_size)

    def undo(self) -> None:
        self._item.set_size(*self._old_size)
        diagram_service.resize_node(self._conn, self._node_id, *self._old_size)
