from models.equipment import Equipment
from models.ground_connection import GroundConnection
from models.power_source import PowerSource
from repositories import diagram_repository
from services import diagram_service, equipment_service, ground_connection_service, power_source_service


def test_power_source_label_uses_kind_not_uuid_fragment(conn, project):
    power = power_source_service.create_power_source(
        conn, PowerSource(power_source_id="", project_id=project.project_id, kind="AC100V")
    )
    node_views, _ = diagram_service.build_diagram_view(conn, project.project_id)
    power_view = next(v for v in node_views if v.node.ref_type == "PowerSource")

    assert power_view.label_lines == ["AC100V"]
    assert power.power_source_id[:4] not in power_view.label_lines


def test_power_source_label_prefers_custom_label(conn, project):
    power_source_service.create_power_source(
        conn, PowerSource(power_source_id="", project_id=project.project_id, kind="ACPowerSupply", label="安定化電源#1")
    )
    node_views, _ = diagram_service.build_diagram_view(conn, project.project_id)
    power_view = next(v for v in node_views if v.node.ref_type == "PowerSource")

    assert power_view.label_lines == ["安定化電源#1"]


def test_ground_label_uses_kind(conn, project):
    ground_connection_service.create_ground_connection(
        conn, GroundConnection(ground_connection_id="", project_id=project.project_id, kind="FG")
    )
    node_views, _ = diagram_service.build_diagram_view(conn, project.project_id)
    ground_view = next(v for v in node_views if v.node.ref_type == "GroundConnection")

    assert ground_view.label_lines == ["FG"]


def test_set_node_colors_persists(conn, project):
    equipment = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project.project_id, display_id="A", category="EUT")
    )
    node = diagram_repository.get_node_by_ref(conn, project.project_id, "Equipment", equipment.equipment_id)

    diagram_service.set_node_colors(conn, node.node_id, "#ff0000", "#00ff00")
    reloaded = diagram_repository.get_node(conn, node.node_id)
    assert reloaded.fill_color == "#ff0000"
    assert reloaded.stroke_color == "#00ff00"

    diagram_service.set_node_colors(conn, node.node_id, None, None)
    reloaded_again = diagram_repository.get_node(conn, node.node_id)
    assert reloaded_again.fill_color is None
    assert reloaded_again.stroke_color is None


def test_set_edge_color_persists(conn, project):
    from models.cable import Cable
    from services import cable_service

    a = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project.project_id, display_id="A", category="EUT")
    )
    b = equipment_service.create_equipment(
        conn, Equipment(equipment_id="", project_id=project.project_id, display_id="B", category="Peripheral")
    )
    cable = cable_service.create_cable(
        conn, Cable(cable_id="", project_id=project.project_id, from_equipment_id=a.equipment_id, to_equipment_id=b.equipment_id)
    )
    edge = diagram_repository.get_edge_by_ref(conn, project.project_id, "Cable", cable.cable_id)

    diagram_service.set_edge_color(conn, edge.edge_id, "#0000ff")
    reloaded = diagram_repository.get_edge(conn, edge.edge_id)
    assert reloaded.line_color == "#0000ff"
