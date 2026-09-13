from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from models.cable import Cable
from models.diagram import DEFAULT_NODE_HEIGHT, DEFAULT_NODE_WIDTH, DiagramEdge, DiagramNode
from models.equipment import Equipment
from models.ground_connection import GroundConnection
from models.power_source import PowerSource
from repositories import cable_repository, diagram_repository, equipment_repository


CHILD_NODE_WIDTH = 70.0
CHILD_NODE_HEIGHT = 36.0
CHILD_LEFT_MARGIN = 14.0
CHILD_TOP_MARGIN = 38.0  # 親ラベル（表示ID+機器名の2行、各16px）と重ならないための余白


@dataclass
class DiagramNodeView:
    node: DiagramNode
    label_lines: list[str] = field(default_factory=list)
    shape: str = "rect"  # "rect" / "ellipse" / "ground"


@dataclass
class DiagramEdgeView:
    edge: DiagramEdge
    from_node_id: str | None
    to_node_id: str | None
    label_lines: list[str] = field(default_factory=list)


# --- Equipment との同期 ---


def ensure_node_for_equipment(conn: sqlite3.Connection, equipment: Equipment) -> DiagramNode:
    node = diagram_repository.get_node_by_ref(
        conn, equipment.project_id, "Equipment", equipment.equipment_id
    )
    parent_node_id = _resolve_parent_node_id(conn, equipment)

    if node is None:
        if parent_node_id is not None:
            relative_x, relative_y = _next_child_position(conn, equipment.project_id, parent_node_id)
            node = DiagramNode(
                node_id="",
                project_id=equipment.project_id,
                ref_type="Equipment",
                ref_id=equipment.equipment_id,
                parent_node_id=parent_node_id,
                relative_x=relative_x,
                relative_y=relative_y,
                width=CHILD_NODE_WIDTH,
                height=CHILD_NODE_HEIGHT,
            )
        else:
            x, y = _next_default_position(conn, equipment.project_id)
            node = DiagramNode(
                node_id="",
                project_id=equipment.project_id,
                ref_type="Equipment",
                ref_id=equipment.equipment_id,
                parent_node_id=None,
                x=x,
                y=y,
                width=DEFAULT_NODE_WIDTH,
                height=DEFAULT_NODE_HEIGHT,
            )
        return diagram_repository.add_node(conn, node)

    if node.parent_node_id != parent_node_id:
        node.parent_node_id = parent_node_id
        diagram_repository.update_node(conn, node)
    return node


def _resolve_parent_node_id(conn: sqlite3.Connection, equipment: Equipment) -> str | None:
    if not equipment.parent_equipment_id:
        return None
    parent_equipment = equipment_repository.get(conn, equipment.parent_equipment_id)
    if parent_equipment is None:
        return None
    parent_node = diagram_repository.get_node_by_ref(
        conn, equipment.project_id, "Equipment", parent_equipment.equipment_id
    )
    return parent_node.node_id if parent_node else None


def delete_node_for_ref(conn: sqlite3.Connection, project_id: str, ref_type: str, ref_id: str) -> None:
    diagram_repository.delete_node_by_ref(conn, project_id, ref_type, ref_id)


# --- PowerSource / GroundConnection との同期 ---


def ensure_node_for_power_source(conn: sqlite3.Connection, power_source: PowerSource) -> DiagramNode:
    node = diagram_repository.get_node_by_ref(
        conn, power_source.project_id, "PowerSource", power_source.power_source_id
    )
    if node is None:
        x, y = _next_default_position(conn, power_source.project_id)
        node = DiagramNode(
            node_id="",
            project_id=power_source.project_id,
            ref_type="PowerSource",
            ref_id=power_source.power_source_id,
            x=x,
            y=y,
            width=60,
            height=60,
        )
        node = diagram_repository.add_node(conn, node)
    return node


def ensure_node_for_ground(conn: sqlite3.Connection, ground: GroundConnection) -> DiagramNode:
    node = diagram_repository.get_node_by_ref(
        conn, ground.project_id, "GroundConnection", ground.ground_connection_id
    )
    if node is None:
        x, y = _next_default_position(conn, ground.project_id)
        node = DiagramNode(
            node_id="",
            project_id=ground.project_id,
            ref_type="GroundConnection",
            ref_id=ground.ground_connection_id,
            x=x,
            y=y,
            width=50,
            height=50,
        )
        node = diagram_repository.add_node(conn, node)
    return node


# --- Cable との同期 ---


def ensure_edge_for_cable(conn: sqlite3.Connection, cable: Cable) -> DiagramEdge:
    edge = diagram_repository.get_edge_by_ref(conn, cable.project_id, "Cable", cable.cable_id)
    if edge is None:
        edge = DiagramEdge(edge_id="", project_id=cable.project_id, ref_type="Cable", ref_id=cable.cable_id)
        edge = diagram_repository.add_edge(conn, edge)
    return edge


def delete_edge_for_ref(conn: sqlite3.Connection, project_id: str, ref_type: str, ref_id: str) -> None:
    diagram_repository.delete_edge_by_ref(conn, project_id, ref_type, ref_id)


# --- 位置・サイズ変更 ---


def move_node(conn: sqlite3.Connection, node_id: str, x: float, y: float) -> None:
    node = diagram_repository.get_node(conn, node_id)
    if node is None:
        return
    if node.parent_node_id is None:
        node.x, node.y = x, y
    else:
        node.relative_x, node.relative_y = x, y
    diagram_repository.update_node(conn, node)


def update_edge_route(conn: sqlite3.Connection, edge_id: str, route_points: list[tuple[float, float]]) -> None:
    """ケーブル線の中間点（折れ線ルート）を更新する。他図形との重なりを避けたい場合に
    直線を複数組み合わせて迂回させるための機能（30.節）。曲線は採用しない。"""
    edge = diagram_repository.get_edge(conn, edge_id)
    if edge is None:
        return
    edge.route_points = route_points
    diagram_repository.update_edge(conn, edge)


def resize_node(conn: sqlite3.Connection, node_id: str, width: float, height: float) -> None:
    node = diagram_repository.get_node(conn, node_id)
    if node is None:
        return
    node.width = max(width, 20)
    node.height = max(height, 20)
    diagram_repository.update_node(conn, node)


def _next_child_position(conn: sqlite3.Connection, project_id: str, parent_node_id: str) -> tuple[float, float]:
    """新規の内包子Nodeが親を完全に覆い隠さないよう、親より小さいサイズ・余白付きの
    位置を初期値として与える（25.節：子は親の枠内に描画する）。既存の兄弟Nodeの数に応じて
    横に並べる簡易配置とし、詳細な調整は自動配置または手動ドラッグに委ねる。"""
    siblings = [
        n for n in diagram_repository.list_nodes_by_project(conn, project_id) if n.parent_node_id == parent_node_id
    ]
    index = len(siblings)
    x = CHILD_LEFT_MARGIN + index * (CHILD_NODE_WIDTH + CHILD_LEFT_MARGIN)
    y = CHILD_TOP_MARGIN
    return x, y


def _next_default_position(conn: sqlite3.Connection, project_id: str) -> tuple[float, float]:
    existing_count = len(
        [n for n in diagram_repository.list_nodes_by_project(conn, project_id) if n.parent_node_id is None]
    )
    col = existing_count % 5
    row = existing_count // 5
    return (60 + col * 200, 60 + row * 160)


# --- 表示用データの組み立て ---


def build_diagram_view(
    conn: sqlite3.Connection, project_id: str
) -> tuple[list[DiagramNodeView], list[DiagramEdgeView]]:
    nodes = diagram_repository.list_nodes_by_project(conn, project_id)
    equipments = {e.equipment_id: e for e in equipment_repository.list_by_project(conn, project_id)}

    node_views: list[DiagramNodeView] = []
    for node in nodes:
        if node.ref_type == "Equipment":
            equipment = equipments.get(node.ref_id)
            if equipment is None:
                continue
            label_lines = [equipment.display_id, equipment.description or equipment.model_name]
            node_views.append(DiagramNodeView(node=node, label_lines=label_lines, shape="rect"))
        elif node.ref_type == "PowerSource":
            node_views.append(DiagramNodeView(node=node, label_lines=[node.ref_id[:4]], shape="ellipse"))
        elif node.ref_type == "GroundConnection":
            node_views.append(DiagramNodeView(node=node, label_lines=[], shape="ground"))

    cables = cable_repository.list_by_project(conn, project_id)
    edges = diagram_repository.list_edges_by_project(conn, project_id)
    edge_by_cable_id = {e.ref_id: e for e in edges if e.ref_type == "Cable"}

    edge_views: list[DiagramEdgeView] = []
    for cable in cables:
        edge = edge_by_cable_id.get(cable.cable_id)
        if edge is None:
            continue
        from_node = diagram_repository.get_node_by_ref(conn, project_id, "Equipment", cable.from_equipment_id)
        to_node = diagram_repository.get_node_by_ref(conn, project_id, "Equipment", cable.to_equipment_id)
        label_lines = [str(cable.cable_no), cable.cable_type] if cable.cable_type else [str(cable.cable_no)]
        edge_views.append(
            DiagramEdgeView(
                edge=edge,
                from_node_id=from_node.node_id if from_node else None,
                to_node_id=to_node.node_id if to_node else None,
                label_lines=label_lines,
            )
        )

    return node_views, edge_views
