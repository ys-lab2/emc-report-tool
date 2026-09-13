import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from diagram.items.cable_item import _distance_to_segment
from models.cable import Cable
from models.equipment import Equipment
from repositories import diagram_repository
from services import cable_service, equipment_service, project_service
from ui.pages.diagram_page import DiagramPage


@pytest.fixture(scope="module")
def qapp():
    yield QApplication.instance() or QApplication([])


def test_distance_to_segment_on_line():
    d = _distance_to_segment(QPointF(5, 0), QPointF(0, 0), QPointF(10, 0))
    assert d == pytest.approx(0.0, abs=1e-6)


def test_distance_to_segment_perpendicular():
    d = _distance_to_segment(QPointF(5, 3), QPointF(0, 0), QPointF(10, 0))
    assert d == pytest.approx(3.0, abs=1e-6)


def test_distance_to_segment_beyond_endpoint():
    d = _distance_to_segment(QPointF(-5, 0), QPointF(0, 0), QPointF(10, 0))
    assert d == pytest.approx(5.0, abs=1e-6)


def _make_project_with_cable(tmp_path, name):
    handle = project_service.create_new(tmp_path / name)
    conn = handle.connection
    project_id = handle.project.project_id

    a = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project_id, display_id="A", category="EUT")
    )
    b = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project_id, display_id="B", category="Peripheral")
    )
    cable = cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project_id, from_equipment_id=a.equipment_id, to_equipment_id=b.equipment_id)
    )
    return handle, cable


def test_route_change_persists_and_supports_undo(qapp, tmp_path):
    handle, cable = _make_project_with_cable(tmp_path, "PJ_ROUTE1.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    page = DiagramPage()
    page.set_project(handle)

    edge = diagram_repository.get_edge_by_ref(conn, project_id, "Cable", cable.cable_id)
    item = page.scene._items_by_edge_id[edge.edge_id]

    old_points = list(item.route_points)
    new_points = [QPointF(100, 50), QPointF(150, 120)]
    item.route_changed.emit(edge.edge_id, old_points, new_points)

    reloaded = diagram_repository.get_edge(conn, edge.edge_id)
    assert reloaded.route_points == [(100.0, 50.0), (150.0, 120.0)]

    page.undo_stack.undo()
    reloaded_after_undo = diagram_repository.get_edge(conn, edge.edge_id)
    assert reloaded_after_undo.route_points == []

    page.undo_stack.redo()
    reloaded_after_redo = diagram_repository.get_edge(conn, edge.edge_id)
    assert reloaded_after_redo.route_points == [(100.0, 50.0), (150.0, 120.0)]

    handle.close()


def test_route_reproduced_after_reopen(tmp_path):
    project_path = tmp_path / "PJ_ROUTE2.emcproj"
    handle, cable = _make_project_with_cable(tmp_path, "PJ_ROUTE2.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    edge = diagram_repository.get_edge_by_ref(conn, project_id, "Cable", cable.cable_id)
    from services import diagram_service

    diagram_service.update_edge_route(conn, edge.edge_id, [(80.0, 40.0), (200.0, 90.0)])
    project_service.save(handle)
    handle.close()

    reopened = project_service.open_project(project_path)
    reloaded_edge = diagram_repository.get_edge_by_ref(
        reopened.connection, reopened.project.project_id, "Cable", cable.cable_id
    )
    assert reloaded_edge.route_points == [(80.0, 40.0), (200.0, 90.0)]
    reopened.close()


def test_point_index_hit_and_segment_insert_index(qapp, tmp_path):
    handle, cable = _make_project_with_cable(tmp_path, "PJ_ROUTE3.emcproj")
    conn = handle.connection
    project_id = handle.project.project_id

    page = DiagramPage()
    page.set_project(handle)

    edge = diagram_repository.get_edge_by_ref(conn, project_id, "Cable", cable.cable_id)
    item = page.scene._items_by_edge_id[edge.edge_id]

    path = item.full_path()
    midpoint = QPointF((path[0].x() + path[1].x()) / 2, (path[0].y() + path[1].y()) / 2)

    insert_index = item._segment_insert_index_at(midpoint)
    assert insert_index == 0

    item.set_route_points([midpoint])
    assert item._point_index_at(midpoint) == 0
    assert item._point_index_at(QPointF(midpoint.x() + 1000, midpoint.y() + 1000)) is None

    handle.close()
