from __future__ import annotations

import sqlite3

from models.cable import Cable
from repositories import cable_repository, equipment_repository, ground_connection_repository, power_source_repository
from services import diagram_service


class InvalidEquipmentReferenceError(Exception):
    """存在しない接続先（Equipment/PowerSource/GroundConnection）が指定された場合の例外（58.節）。"""


def _ref_exists(conn: sqlite3.Connection, ref_type: str, ref_id: str) -> bool:
    if not ref_id:
        return False
    if ref_type == "Equipment":
        return equipment_repository.get(conn, ref_id) is not None
    if ref_type == "PowerSource":
        return power_source_repository.get(conn, ref_id) is not None
    if ref_type == "GroundConnection":
        return ground_connection_repository.get(conn, ref_id) is not None
    return False


def _validate_endpoints(conn: sqlite3.Connection, cable: Cable) -> None:
    if not _ref_exists(conn, cable.from_ref_type, cable.from_ref_id):
        raise InvalidEquipmentReferenceError("From接続先が存在しません。")
    if not _ref_exists(conn, cable.to_ref_type, cable.to_ref_id):
        raise InvalidEquipmentReferenceError("To接続先が存在しません。")


def create_cable(conn: sqlite3.Connection, cable: Cable) -> Cable:
    _validate_endpoints(conn, cable)
    if not cable.cable_no:
        cable.cable_no = cable_repository.next_cable_no(conn, cable.project_id)
    created = cable_repository.add(conn, cable)
    diagram_service.ensure_edge_for_cable(conn, created)
    return created


def update_cable(conn: sqlite3.Connection, cable: Cable) -> None:
    _validate_endpoints(conn, cable)
    cable_repository.update(conn, cable)
    diagram_service.ensure_edge_for_cable(conn, cable)


def delete_cable(conn: sqlite3.Connection, cable_id: str) -> None:
    cable = cable_repository.get(conn, cable_id)
    if cable is None:
        return
    cable_repository.delete(conn, cable_id)
    diagram_service.delete_edge_for_ref(conn, cable.project_id, "Cable", cable_id)
