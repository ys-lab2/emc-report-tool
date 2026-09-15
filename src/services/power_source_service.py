from __future__ import annotations

import sqlite3

from models.power_source import PowerSource
from repositories import cable_repository, power_source_repository
from services import diagram_service


def create_power_source(conn: sqlite3.Connection, power_source: PowerSource) -> PowerSource:
    created = power_source_repository.add(conn, power_source)
    diagram_service.ensure_node_for_power_source(conn, created)
    return created


def update_power_source(conn: sqlite3.Connection, power_source: PowerSource) -> None:
    power_source_repository.update(conn, power_source)


def delete_power_source(conn: sqlite3.Connection, power_source_id: str) -> None:
    power_source = power_source_repository.get(conn, power_source_id)
    if power_source is None:
        return

    for cable in cable_repository.list_by_project(conn, power_source.project_id):
        if (cable.from_ref_type == "PowerSource" and cable.from_ref_id == power_source_id) or (
            cable.to_ref_type == "PowerSource" and cable.to_ref_id == power_source_id
        ):
            diagram_service.delete_edge_for_ref(conn, power_source.project_id, "Cable", cable.cable_id)
    cable_repository.delete_by_ref(conn, "PowerSource", power_source_id)

    power_source_repository.delete(conn, power_source_id)
    diagram_service.delete_node_for_ref(conn, power_source.project_id, "PowerSource", power_source_id)
