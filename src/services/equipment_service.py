from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from models.equipment import Equipment
from repositories import equipment_repository
from services import diagram_service


class CircularContainmentError(Exception):
    """自己参照または循環参照になる親子設定が指定された場合の例外。"""


@dataclass
class DeletionImpact:
    referencing_cable_count: int
    direct_children: list[Equipment]

    @property
    def has_warnings(self) -> bool:
        return self.referencing_cable_count > 0 or bool(self.direct_children)


def _get_descendant_ids(conn: sqlite3.Connection, equipment_id: str) -> set[str]:
    descendants: set[str] = set()
    stack = [equipment_id]
    while stack:
        current_id = stack.pop()
        for child in equipment_repository.list_children(conn, current_id):
            if child.equipment_id not in descendants:
                descendants.add(child.equipment_id)
                stack.append(child.equipment_id)
    return descendants


def validate_parent_assignment(
    conn: sqlite3.Connection, equipment_id: str, parent_equipment_id: str | None
) -> None:
    """自己参照・循環参照を検出する（14.節・15.節）。多段階の内包を正しく辿るため
    equipment_idの子孫すべてをたどり、parent_equipment_idがその中に含まれないか確認する。"""
    if parent_equipment_id is None:
        return
    if parent_equipment_id == equipment_id:
        raise CircularContainmentError("自分自身を親機器に設定することはできません。")

    descendants = _get_descendant_ids(conn, equipment_id)
    if parent_equipment_id in descendants:
        raise CircularContainmentError(
            "指定した親機器はこの機器の内包先（子孫）になっているため、"
            "循環参照になります。"
        )


def get_ineligible_parent_ids(conn: sqlite3.Connection, equipment_id: str | None) -> set[str]:
    """親機器の選択肢から除外すべきID集合（自分自身＋自分の子孫）を返す。
    新規作成中（equipment_idがNone）の場合は除外対象なし。"""
    if not equipment_id:
        return set()
    return {equipment_id} | _get_descendant_ids(conn, equipment_id)


def create_equipment(conn: sqlite3.Connection, equipment: Equipment) -> Equipment:
    validate_parent_assignment(conn, equipment.equipment_id or "__new__", equipment.parent_equipment_id)
    created = equipment_repository.add(conn, equipment)
    diagram_service.ensure_node_for_equipment(conn, created)
    return created


def update_equipment(conn: sqlite3.Connection, equipment: Equipment) -> None:
    validate_parent_assignment(conn, equipment.equipment_id, equipment.parent_equipment_id)
    equipment_repository.update(conn, equipment)
    diagram_service.ensure_node_for_equipment(conn, equipment)


def get_deletion_impact(conn: sqlite3.Connection, equipment_id: str) -> DeletionImpact:
    cable_count = equipment_repository.count_cables_referencing(conn, equipment_id)
    children = equipment_repository.list_children(conn, equipment_id)
    return DeletionImpact(referencing_cable_count=cable_count, direct_children=children)


def delete_equipment(
    conn: sqlite3.Connection, equipment_id: str, cascade_children: bool
) -> None:
    """機器を削除する。cascade_children=Trueなら子機器も再帰的に削除し、
    Falseなら子機器を独立機器に変更してから削除する（57.節）。
    参照しているCableはDB外部キーのON DELETE CASCADEにより自動的に削除される。"""
    equipment = equipment_repository.get(conn, equipment_id)
    if equipment is None:
        return

    children = equipment_repository.list_children(conn, equipment_id)
    if children:
        if cascade_children:
            for child in children:
                delete_equipment(conn, child.equipment_id, cascade_children=True)
        else:
            equipment_repository.clear_parent_for_children(conn, equipment_id)

    equipment_repository.delete(conn, equipment_id)
    diagram_service.delete_node_for_ref(conn, equipment.project_id, "Equipment", equipment_id)


def next_display_id(conn: sqlite3.Connection, project_id: str) -> str:
    """既存のdisplay_idの中で最も後ろのアルファベットの次を返す簡易的な自動採番。
    A, B, ... Z, AA, AB ... の順。厳密な一意性はUI側の警告表示で担保する（58.節）。"""
    existing = {e.display_id for e in equipment_repository.list_by_project(conn, project_id)}
    index = 0
    while True:
        candidate = _index_to_letters(index)
        if candidate not in existing:
            return candidate
        index += 1


def _index_to_letters(index: int) -> str:
    letters = ""
    n = index
    while True:
        n, remainder = divmod(n, 26)
        letters = chr(ord("A") + remainder) + letters
        if n == 0:
            break
        n -= 1
    return letters
