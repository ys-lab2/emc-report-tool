import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from diagram.items.equipment_item import EquipmentItem
from models.cable import Cable
from models.equipment import Equipment
from repositories import diagram_repository
from services import cable_service, equipment_service, project_service
from ui.pages.diagram_page import DiagramPage


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


def _make_project_with_equipment(tmp_path, name):
    handle = project_service.create_new(tmp_path / name)
    conn = handle.connection
    project_id = handle.project.project_id

    a = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project_id, display_id="A", category="EUT")
    )
    b = equipment_service.create_equipment(
        conn,
        Equipment(
            equipment_id="",
            project_id=project_id,
            display_id="B",
            category="EUT",
            placement_type="embedded",
            parent_equipment_id=a.equipment_id,
        ),
    )
    c = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project_id, display_id="C", category="Peripheral")
    )
    cable_service.create_cable(
        conn,
        Cable(cable_id="", project_id=project_id, from_ref_id=a.equipment_id, to_ref_id=c.equipment_id, cable_type="USB"),
    )
    return handle, a, b, c


def test_diagram_scene_builds_items_with_correct_hierarchy(qapp, tmp_path):
    handle, a, b, c = _make_project_with_equipment(tmp_path, "PJ_DIAG1.emcproj")

    page = DiagramPage()
    page.set_project(handle)

    node_a = diagram_repository.get_node_by_ref(handle.connection, handle.project.project_id, "Equipment", a.equipment_id)
    node_b = diagram_repository.get_node_by_ref(handle.connection, handle.project.project_id, "Equipment", b.equipment_id)

    item_a = page.scene._items_by_node_id[node_a.node_id]
    item_b = page.scene._items_by_node_id[node_b.node_id]

    assert item_b.parentItem() is item_a
    assert len(page.scene.items()) >= 4  # 3 equipment + 1 cable

    handle.close()


def test_move_node_persists_and_supports_undo(qapp, tmp_path):
    handle, a, b, c = _make_project_with_equipment(tmp_path, "PJ_DIAG2.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    page = DiagramPage()
    page.set_project(handle)

    node_a = diagram_repository.get_node_by_ref(conn, project_id, "Equipment", a.equipment_id)
    item_a: EquipmentItem = page.scene._items_by_node_id[node_a.node_id]

    old_pos = (item_a.pos().x(), item_a.pos().y())
    item_a.move_finished.emit(node_a.node_id, old_pos[0], old_pos[1], old_pos[0] + 50, old_pos[1] + 30)

    reloaded = diagram_repository.get_node(conn, node_a.node_id)
    assert reloaded.x == old_pos[0] + 50
    assert reloaded.y == old_pos[1] + 30

    page.undo_stack.undo()
    reloaded_after_undo = diagram_repository.get_node(conn, node_a.node_id)
    assert reloaded_after_undo.x == old_pos[0]
    assert reloaded_after_undo.y == old_pos[1]

    page.undo_stack.redo()
    reloaded_after_redo = diagram_repository.get_node(conn, node_a.node_id)
    assert reloaded_after_redo.x == old_pos[0] + 50

    handle.close()


def test_resize_node_persists_and_supports_undo(qapp, tmp_path):
    handle, a, b, c = _make_project_with_equipment(tmp_path, "PJ_DIAG3.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    page = DiagramPage()
    page.set_project(handle)

    node_a = diagram_repository.get_node_by_ref(conn, project_id, "Equipment", a.equipment_id)
    item_a: EquipmentItem = page.scene._items_by_node_id[node_a.node_id]

    old_size = (item_a.width, item_a.height)
    item_a.resize_finished.emit(node_a.node_id, old_size[0], old_size[1], old_size[0] + 40, old_size[1] + 20)

    reloaded = diagram_repository.get_node(conn, node_a.node_id)
    assert reloaded.width == old_size[0] + 40
    assert reloaded.height == old_size[1] + 20

    page.undo_stack.undo()
    reloaded_after_undo = diagram_repository.get_node(conn, node_a.node_id)
    assert reloaded_after_undo.width == old_size[0]

    handle.close()


def test_auto_layout_button_updates_positions(qapp, tmp_path):
    handle, a, b, c = _make_project_with_equipment(tmp_path, "PJ_DIAG4.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    page = DiagramPage()
    page.set_project(handle)

    from diagram.layout import auto_layout

    auto_layout.layout_all(conn, project_id)
    page.refresh()

    node_c = diagram_repository.get_node_by_ref(conn, project_id, "Equipment", c.equipment_id)
    node_a = diagram_repository.get_node_by_ref(conn, project_id, "Equipment", a.equipment_id)
    assert node_c.x < node_a.x  # Peripheral(C) is left of EUT(A)

    handle.close()


def test_diagram_reproduced_identically_after_reopen(qapp, tmp_path):
    project_path = tmp_path / "PJ_DIAG5.emcproj"
    handle, a, b, c = _make_project_with_equipment(tmp_path, "PJ_DIAG5.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    node_a = diagram_repository.get_node_by_ref(conn, project_id, "Equipment", a.equipment_id)
    from services import diagram_service

    diagram_service.move_node(conn, node_a.node_id, 321.0, 654.0)
    diagram_service.resize_node(conn, node_a.node_id, 200.0, 150.0)
    project_service.save(handle)
    handle.close()

    reopened = project_service.open_project(project_path)
    reloaded_node = diagram_repository.get_node_by_ref(
        reopened.connection, reopened.project.project_id, "Equipment", a.equipment_id
    )
    assert reloaded_node.x == 321.0
    assert reloaded_node.y == 654.0
    assert reloaded_node.width == 200.0
    assert reloaded_node.height == 150.0

    reopened.close()
