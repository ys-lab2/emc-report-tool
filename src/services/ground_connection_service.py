from __future__ import annotations

import sqlite3

from models.ground_connection import GroundConnection
from repositories import cable_repository, ground_connection_repository
from services import diagram_service


def create_ground_connection(conn: sqlite3.Connection, ground: GroundConnection) -> GroundConnection:
    created = ground_connection_repository.add(conn, ground)
    diagram_service.ensure_node_for_ground(conn, created)
    return created


def update_ground_connection(conn: sqlite3.Connection, ground: GroundConnection) -> None:
    ground_connection_repository.update(conn, ground)


def delete_ground_connection(conn: sqlite3.Connection, ground_connection_id: str) -> None:
    ground = ground_connection_repository.get(conn, ground_connection_id)
    if ground is None:
        return

    for cable in cable_repository.list_by_project(conn, ground.project_id):
        if (cable.from_ref_type == "GroundConnection" and cable.from_ref_id == ground_connection_id) or (
            cable.to_ref_type == "GroundConnection" and cable.to_ref_id == ground_connection_id
        ):
            diagram_service.delete_edge_for_ref(conn, ground.project_id, "Cable", cable.cable_id)
    cable_repository.delete_by_ref(conn, "GroundConnection", ground_connection_id)

    ground_connection_repository.delete(conn, ground_connection_id)
    diagram_service.delete_node_for_ref(conn, ground.project_id, "GroundConnection", ground_connection_id)
