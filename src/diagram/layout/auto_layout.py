from __future__ import annotations

import sqlite3

from repositories import diagram_repository, equipment_repository

TOP_ROW_Y = 40.0
EUT_COLUMN_X = 520.0
PERIPHERAL_COLUMN_X = 160.0
ASSOCIATED_COLUMN_X = 880.0
BOTTOM_ROW_Y = 640.0
ROW_SPACING = 170.0
COLUMN_START_Y = 220.0

CHILD_MARGIN = 14.0
CHILD_SPACING = 8.0


def layout_all(conn: sqlite3.Connection, project_id: str) -> None:
    """32.節のカテゴリ別配置ルールに基づき、トップレベルNodeを再配置する。
    内包されている子Nodeは親の枠内にグリッド状に配置し直す。
    既存の手動調整をすべて上書きするため、呼び出し側で確認を取ってから実行すること。"""
    nodes = diagram_repository.list_nodes_by_project(conn, project_id)
    equipments = {e.equipment_id: e for e in equipment_repository.list_by_project(conn, project_id)}

    top_level = [n for n in nodes if n.parent_node_id is None]
    nodes_by_parent: dict[str, list] = {}
    for n in nodes:
        if n.parent_node_id:
            nodes_by_parent.setdefault(n.parent_node_id, []).append(n)

    peripheral_nodes = []
    eut_nodes = []
    associated_nodes = []
    other_nodes = []
    power_nodes = []
    ground_nodes = []

    for node in top_level:
        if node.ref_type == "PowerSource":
            power_nodes.append(node)
        elif node.ref_type == "GroundConnection":
            ground_nodes.append(node)
        elif node.ref_type == "Equipment":
            equipment = equipments.get(node.ref_id)
            category = equipment.category if equipment else "Other"
            if category == "EUT":
                eut_nodes.append(node)
            elif category == "Peripheral":
                peripheral_nodes.append(node)
            elif category == "AssociatedEquipment":
                associated_nodes.append(node)
            else:
                other_nodes.append(node)

    _stack_vertically(eut_nodes, EUT_COLUMN_X)
    _stack_vertically(peripheral_nodes, PERIPHERAL_COLUMN_X)
    _stack_vertically(associated_nodes, ASSOCIATED_COLUMN_X)
    _stack_vertically(other_nodes, EUT_COLUMN_X, start_y=COLUMN_START_Y + ROW_SPACING * (len(eut_nodes) + 1))
    _stack_horizontally(power_nodes, TOP_ROW_Y)
    _stack_horizontally(ground_nodes, BOTTOM_ROW_Y)

    for node in top_level:
        diagram_repository.update_node(conn, node)

    for parent_node_id, children in nodes_by_parent.items():
        parent = next((n for n in nodes if n.node_id == parent_node_id), None)
        if parent is None:
            continue
        _layout_children(parent, children)
        for child in children:
            diagram_repository.update_node(conn, child)


def _stack_vertically(nodes: list, x: float, start_y: float = COLUMN_START_Y) -> None:
    for index, node in enumerate(nodes):
        node.x = x - node.width / 2
        node.y = start_y + index * ROW_SPACING


def _stack_horizontally(nodes: list, y: float) -> None:
    start_x = EUT_COLUMN_X - (len(nodes) - 1) * 90 / 2 if nodes else EUT_COLUMN_X
    for index, node in enumerate(nodes):
        node.x = start_x + index * 90
        node.y = y


def _layout_children(parent, children: list) -> None:
    available_width = max(parent.width - 2 * CHILD_MARGIN, 40)
    cursor_x = CHILD_MARGIN
    cursor_y = CHILD_MARGIN + 20  # 親のラベル分の余白
    row_height = 0.0

    for child in children:
        if cursor_x + child.width > available_width + CHILD_MARGIN and cursor_x > CHILD_MARGIN:
            cursor_x = CHILD_MARGIN
            cursor_y += row_height + CHILD_SPACING
            row_height = 0.0

        child.relative_x = cursor_x
        child.relative_y = cursor_y
        cursor_x += child.width + CHILD_SPACING
        row_height = max(row_height, child.height)
