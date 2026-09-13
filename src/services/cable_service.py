from __future__ import annotations

import sqlite3

from models.cable import Cable
from repositories import cable_repository, equipment_repository
from services import diagram_service


class InvalidEquipmentReferenceError(Exception):
    """存在しないEquipmentへのFrom/To参照が指定された場合の例外（58.節）。"""


def _validate_endpoints(conn: sqlite3.Connection, cable: Cable) -> None:
    if not cable.from_equipment_id or equipment_repository.get(conn, cable.from_equipment_id) is None:
        raise InvalidEquipmentReferenceError("From機器が存在しません。")
    if not cable.to_equipment_id or equipment_repository.get(conn, cable.to_equipment_id) is None:
        raise InvalidEquipmentReferenceError("To機器が存在しません。")


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
