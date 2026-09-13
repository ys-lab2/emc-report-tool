from __future__ import annotations

import sqlite3

from models.inline_component import InlineComponent
from repositories import inline_component_repository


def list_for_cable(conn: sqlite3.Connection, cable_id: str) -> list[InlineComponent]:
    return inline_component_repository.list_by_cable(conn, cable_id)


def add_component(conn: sqlite3.Connection, component: InlineComponent) -> InlineComponent:
    return inline_component_repository.add(conn, component)


def update_component(conn: sqlite3.Connection, component: InlineComponent) -> None:
    inline_component_repository.update(conn, component)


def delete_component(conn: sqlite3.Connection, inline_component_id: str) -> None:
    inline_component_repository.delete(conn, inline_component_id)
