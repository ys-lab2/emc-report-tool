from __future__ import annotations

import json
import sqlite3

from models.diagram import DiagramEdge, DiagramNode
from utils.uuid_utils import new_id

# --- DiagramNode ---


def list_nodes_by_project(conn: sqlite3.Connection, project_id: str) -> list[DiagramNode]:
    rows = conn.execute(
        "SELECT * FROM diagram_nodes WHERE project_id = ?", (project_id,)
    ).fetchall()
    return [_row_to_node(row) for row in rows]


def get_node(conn: sqlite3.Connection, node_id: str) -> DiagramNode | None:
    row = conn.execute(
        "SELECT * FROM diagram_nodes WHERE node_id = ?", (node_id,)
    ).fetchone()
    return _row_to_node(row) if row else None


def get_node_by_ref(
    conn: sqlite3.Connection, project_id: str, ref_type: str, ref_id: str
) -> DiagramNode | None:
    row = conn.execute(
        "SELECT * FROM diagram_nodes WHERE project_id = ? AND ref_type = ? AND ref_id = ?",
        (project_id, ref_type, ref_id),
    ).fetchone()
    return _row_to_node(row) if row else None


def add_node(conn: sqlite3.Connection, node: DiagramNode) -> DiagramNode:
    if not node.node_id:
        node.node_id = new_id()
    conn.execute(
        """
        INSERT INTO diagram_nodes
            (node_id, project_id, ref_type, ref_id, parent_node_id, x, y,
             relative_x, relative_y, width, height, z_order, label_dx, label_dy)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            node.node_id,
            node.project_id,
            node.ref_type,
            node.ref_id,
            node.parent_node_id,
            node.x,
            node.y,
            node.relative_x,
            node.relative_y,
            node.width,
            node.height,
            node.z_order,
            node.label_dx,
            node.label_dy,
        ),
    )
    conn.commit()
    return node


def update_node(conn: sqlite3.Connection, node: DiagramNode) -> None:
    conn.execute(
        """
        UPDATE diagram_nodes SET
            parent_node_id = ?, x = ?, y = ?, relative_x = ?, relative_y = ?,
            width = ?, height = ?, z_order = ?, label_dx = ?, label_dy = ?
        WHERE node_id = ?
        """,
        (
            node.parent_node_id,
            node.x,
            node.y,
            node.relative_x,
            node.relative_y,
            node.width,
            node.height,
            node.z_order,
            node.label_dx,
            node.label_dy,
            node.node_id,
        ),
    )
    conn.commit()


def delete_node(conn: sqlite3.Connection, node_id: str) -> None:
    conn.execute("DELETE FROM diagram_nodes WHERE node_id = ?", (node_id,))
    conn.commit()


def delete_node_by_ref(conn: sqlite3.Connection, project_id: str, ref_type: str, ref_id: str) -> None:
    conn.execute(
        "DELETE FROM diagram_nodes WHERE project_id = ? AND ref_type = ? AND ref_id = ?",
        (project_id, ref_type, ref_id),
    )
    conn.commit()


def _row_to_node(row: sqlite3.Row) -> DiagramNode:
    return DiagramNode(
        node_id=row["node_id"],
        project_id=row["project_id"],
        ref_type=row["ref_type"],
        ref_id=row["ref_id"],
        parent_node_id=row["parent_node_id"],
        x=row["x"],
        y=row["y"],
        relative_x=row["relative_x"],
        relative_y=row["relative_y"],
        width=row["width"],
        height=row["height"],
        z_order=row["z_order"],
        label_dx=row["label_dx"],
        label_dy=row["label_dy"],
    )


# --- DiagramEdge ---


def list_edges_by_project(conn: sqlite3.Connection, project_id: str) -> list[DiagramEdge]:
    rows = conn.execute(
        "SELECT * FROM diagram_edges WHERE project_id = ?", (project_id,)
    ).fetchall()
    return [_row_to_edge(row) for row in rows]


def get_edge(conn: sqlite3.Connection, edge_id: str) -> DiagramEdge | None:
    row = conn.execute(
        "SELECT * FROM diagram_edges WHERE edge_id = ?", (edge_id,)
    ).fetchone()
    return _row_to_edge(row) if row else None


def get_edge_by_ref(
    conn: sqlite3.Connection, project_id: str, ref_type: str, ref_id: str
) -> DiagramEdge | None:
    row = conn.execute(
        "SELECT * FROM diagram_edges WHERE project_id = ? AND ref_type = ? AND ref_id = ?",
        (project_id, ref_type, ref_id),
    ).fetchone()
    return _row_to_edge(row) if row else None


def add_edge(conn: sqlite3.Connection, edge: DiagramEdge) -> DiagramEdge:
    if not edge.edge_id:
        edge.edge_id = new_id()
    conn.execute(
        """
        INSERT INTO diagram_edges (edge_id, project_id, ref_type, ref_id, route_points_json, label_dx, label_dy)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            edge.edge_id,
            edge.project_id,
            edge.ref_type,
            edge.ref_id,
            json.dumps(edge.route_points),
            edge.label_dx,
            edge.label_dy,
        ),
    )
    conn.commit()
    return edge


def update_edge(conn: sqlite3.Connection, edge: DiagramEdge) -> None:
    conn.execute(
        "UPDATE diagram_edges SET route_points_json = ?, label_dx = ?, label_dy = ? WHERE edge_id = ?",
        (json.dumps(edge.route_points), edge.label_dx, edge.label_dy, edge.edge_id),
    )
    conn.commit()


def delete_edge_by_ref(conn: sqlite3.Connection, project_id: str, ref_type: str, ref_id: str) -> None:
    conn.execute(
        "DELETE FROM diagram_edges WHERE project_id = ? AND ref_type = ? AND ref_id = ?",
        (project_id, ref_type, ref_id),
    )
    conn.commit()


def _row_to_edge(row: sqlite3.Row) -> DiagramEdge:
    raw_points = row["route_points_json"]
    points = [tuple(p) for p in json.loads(raw_points)] if raw_points else []
    return DiagramEdge(
        edge_id=row["edge_id"],
        project_id=row["project_id"],
        ref_type=row["ref_type"],
        ref_id=row["ref_id"],
        route_points=points,
        label_dx=row["label_dx"],
        label_dy=row["label_dy"],
    )
