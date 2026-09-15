from __future__ import annotations

import sqlite3

from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import QGraphicsScene

from diagram.commands.edge_commands import ChangeEdgeColorCommand, UpdateRouteCommand
from diagram.commands.node_commands import ChangeNodeColorCommand, MoveNodeCommand, ResizeNodeCommand
from diagram.items.base_node_item import NodeItemBase
from diagram.items.cable_item import CableItem
from diagram.items.equipment_item import EquipmentItem
from diagram.items.ground_item import GroundItem
from diagram.items.power_item import PowerSourceItem
from services import diagram_service


class DiagramScene(QGraphicsScene):
    def __init__(self, undo_stack: QUndoStack) -> None:
        super().__init__()
        self._conn: sqlite3.Connection | None = None
        self._project_id: str | None = None
        self._items_by_node_id: dict[str, NodeItemBase] = {}
        self._items_by_edge_id: dict[str, CableItem] = {}
        self.undo_stack = undo_stack

    def set_project(self, conn: sqlite3.Connection, project_id: str) -> None:
        self._conn = conn
        self._project_id = project_id
        self.reload()

    def reload(self) -> None:
        if self._conn is None or self._project_id is None:
            return

        self.clear()
        self._items_by_node_id.clear()
        self._items_by_edge_id.clear()

        node_views, edge_views = diagram_service.build_diagram_view(self._conn, self._project_id)

        children_map: dict[str, list] = {}
        roots = []
        for node_view in node_views:
            if node_view.node.parent_node_id:
                children_map.setdefault(node_view.node.parent_node_id, []).append(node_view)
            else:
                roots.append(node_view)

        for root in roots:
            self._create_item(root, children_map, parent_item=None)

        for edge_view in edge_views:
            from_item = self._items_by_node_id.get(edge_view.from_node_id) if edge_view.from_node_id else None
            to_item = self._items_by_node_id.get(edge_view.to_node_id) if edge_view.to_node_id else None
            if from_item is None or to_item is None:
                continue
            route_points = [QPointF(x, y) for x, y in edge_view.edge.route_points]
            edge_item = CableItem(
                edge_view.edge.edge_id,
                from_item,
                to_item,
                edge_view.label_lines,
                route_points,
                edge_view.edge.line_color,
            )
            edge_item.route_changed.connect(self._on_route_changed)
            edge_item.color_changed.connect(self._on_edge_color_changed)
            self.addItem(edge_item)
            self._items_by_edge_id[edge_view.edge.edge_id] = edge_item

    def _create_item(self, node_view, children_map: dict, parent_item: NodeItemBase | None) -> None:
        node = node_view.node

        if node_view.shape == "rect":
            item: NodeItemBase = EquipmentItem(
                node.node_id, node.width, node.height, node_view.label_lines, node.fill_color, node.stroke_color
            )
            item.clamp_to_parent = node_view.placement_type != "attached"
            item.resize_finished.connect(self._on_resize_finished)
        elif node_view.shape == "ellipse":
            item = PowerSourceItem(
                node.node_id, node.width, node.height, node_view.label_lines, node.fill_color, node.stroke_color
            )
        else:
            item = GroundItem(
                node.node_id, node.width, node.height, node_view.label_lines, node.fill_color, node.stroke_color
            )

        item.move_finished.connect(self._on_move_finished)
        item.colors_changed.connect(self._on_node_colors_changed)

        if parent_item is not None:
            item.setParentItem(parent_item)
            item.setPos(node.relative_x, node.relative_y)
        else:
            self.addItem(item)
            item.setPos(node.x, node.y)

        self._items_by_node_id[node.node_id] = item

        for child_view in children_map.get(node.node_id, []):
            self._create_item(child_view, children_map, item)

    def _on_move_finished(self, node_id: str, old_x: float, old_y: float, new_x: float, new_y: float) -> None:
        item = self._items_by_node_id[node_id]
        command = MoveNodeCommand(self._conn, node_id, item, (old_x, old_y), (new_x, new_y))
        self.undo_stack.push(command)

    def _on_resize_finished(self, node_id: str, old_w: float, old_h: float, new_w: float, new_h: float) -> None:
        item = self._items_by_node_id[node_id]
        command = ResizeNodeCommand(self._conn, node_id, item, (old_w, old_h), (new_w, new_h))
        self.undo_stack.push(command)

    def _on_route_changed(self, edge_id: str, old_points: list, new_points: list) -> None:
        item = self._items_by_edge_id[edge_id]
        command = UpdateRouteCommand(self._conn, edge_id, item, old_points, new_points)
        self.undo_stack.push(command)

    def _on_node_colors_changed(
        self, node_id: str, old_fill: str | None, old_stroke: str | None, new_fill: str | None, new_stroke: str | None
    ) -> None:
        item = self._items_by_node_id[node_id]
        command = ChangeNodeColorCommand(self._conn, node_id, item, (old_fill, old_stroke), (new_fill, new_stroke))
        self.undo_stack.push(command)

    def _on_edge_color_changed(self, edge_id: str, old_color: str | None, new_color: str | None) -> None:
        item = self._items_by_edge_id[edge_id]
        command = ChangeEdgeColorCommand(self._conn, edge_id, item, old_color, new_color)
        self.undo_stack.push(command)
